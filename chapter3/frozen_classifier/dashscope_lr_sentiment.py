import os
import json
import pickle
from hashlib import sha256
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import openai
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

import typer
from tqdm import tqdm


app = typer.Typer(add_completion=False, no_args_is_help=True)


class DashScopeSentimentClassifier:
    """用冻结文本嵌入训练情感分类头，分别检查表示与任务学习。"""

    def __init__(self, model_name: str = "text-embedding-v1", regularization: float = 1.0, load_encoder: bool = True):
        """
        初始化分类器
        
        Args:
            model_name: DashScope 模型名称
        """
        local_name = os.getenv("WORKSHOP_LOCAL_EMBEDDING_MODEL")
        self.model_name = local_name or model_name
        self.local_model = None
        self.embedding_client = None
        if not np.isfinite(regularization) or regularization <= 0:
            raise ValueError("正则化参数 C 必须是有限正数。")
        if not load_encoder:
            pass
        elif local_name:
            from fastembed import TextEmbedding

            print(f"初始化本地嵌入模型: {local_name}")
            self.local_model = TextEmbedding(local_name)
        else:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("配置 DASHSCOPE_API_KEY，或用 WORKSHOP_LOCAL_EMBEDDING_MODEL 选择本地嵌入。")
            print(f"初始化 DashScope Embedding 客户端: {model_name}")
            self.embedding_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

        # 初始化分类器和预处理器
        self.classifier = LogisticRegression(C=regularization, random_state=42, max_iter=1000)
        self.scaler = StandardScaler()
        
        # 存储训练结果
        self.training_history = {}
        
    @staticmethod
    def load_data(file_path: str) -> Tuple[List[str], List[int]]:
        """加载情感分类数据"""
        print(f"加载数据文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        texts = []
        labels = []
        
        if not isinstance(data, list) or not data:
            raise ValueError("输入应为非空的标注记录数组。")
        seen = set()
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get('sentence'), str) or not item['sentence'].strip() or type(item.get('label')) is not int or item['label'] not in (0, 1):
                raise ValueError("每条记录需要非空 sentence 和整数 label（0 或 1）。")
            normalized = item['sentence'].strip()
            if normalized in seen:
                raise ValueError("存在重复文本；请先复核重复与冲突标签，避免同一文本进入训练集和测试集。")
            seen.add(normalized)
            texts.append(item['sentence'])
            labels.append(item['label'])
        
        print(f"加载了 {len(texts)} 条数据")
        print(f"标签分布: 负面={labels.count(0)}, 正面={labels.count(1)}")
        
        return texts, labels
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 10) -> np.ndarray:
        """生成固定特征，分类头训练不会更新嵌入模型。"""
        print("生成冻结文本嵌入...")

        if self.local_model is not None:
            return np.array(list(self.local_model.embed(texts, batch_size=batch_size)))

        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="生成 Embedding"):
            batch = texts[i:i + batch_size]
            response = self.embedding_client.embeddings.create(model=self.model_name, input=batch)
            rows = sorted(response.data, key=lambda row: row.index)
            if [row.index for row in rows] != list(range(len(batch))):
                raise RuntimeError("嵌入返回的行与输入不匹配。")
            embeddings.extend(row.embedding for row in rows)

        embeddings_array = np.vstack(embeddings)
        print(f"Embedding 维度: {embeddings_array.shape}")
        
        return embeddings_array
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray, y_val: np.ndarray) -> Dict:
        """在训练特征上拟合标准化器与逻辑回归分类头。"""
        print("训练逻辑回归分类头...")

        # 标准化特征
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # 训练分类器
        self.classifier.fit(X_train_scaled, y_train)
        
        # 评估训练集和验证集
        train_pred = self.classifier.predict(X_train_scaled)
        val_pred = self.classifier.predict(X_val_scaled)
        
        train_acc = accuracy_score(y_train, train_pred)
        val_acc = accuracy_score(y_val, val_pred)
        
        print(f"训练集准确率: {train_acc:.4f}")
        print(f"验证集准确率: {val_acc:.4f}")
        
        # 保存训练历史
        self.training_history = {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'train_predictions': train_pred,
            'val_predictions': val_pred,
            'feature_importance': self.classifier.coef_[0] if hasattr(self.classifier, 'coef_') else None
        }
        
        return self.training_history
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """评估模型性能"""
        print("评估模型性能...")
        
        X_test_scaled = self.scaler.transform(X_test)
        y_pred = self.classifier.predict(X_test_scaled)
        y_prob = self.classifier.predict_proba(X_test_scaled)
        
        # 计算指标
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, labels=[0, 1], target_names=['负面', '正面'], output_dict=True, zero_division=0)
        conf_matrix = confusion_matrix(y_test, y_pred)
        
        print(f"测试集准确率: {accuracy:.4f}")
        print("\n分类报告:")
        print(classification_report(y_test, y_pred, labels=[0, 1], target_names=['负面', '正面'], zero_division=0))
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'confusion_matrix': conf_matrix,
            'predictions': y_pred,
            'probabilities': y_prob
        }
    
    def predict(self, texts: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """预测新文本的情感"""
        print("预测新文本情感...")
        
        # 生成 Embedding
        embeddings = self.generate_embeddings(texts)
        
        # 标准化
        embeddings_scaled = self.scaler.transform(embeddings)
        
        # 预测
        predictions = self.classifier.predict(embeddings_scaled)
        probabilities = self.classifier.predict_proba(embeddings_scaled)
        
        return predictions, probabilities
    
    def save_model(self, model_path: str):
        """保存模型"""
        print(f"保存模型到: {model_path}")
        
        model_data = {
            'classifier': self.classifier,
            'scaler': self.scaler,
            'model_name': self.model_name,
            'training_history': self.training_history
        }
        
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, model_path: str):
        """加载模型"""
        print(f"加载模型从: {model_path}")
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        saved_model = model_data.get('model_name', self.model_name)
        if saved_model != self.model_name:
            raise ValueError(
                f"分类器使用 {saved_model} 的嵌入，当前为 {self.model_name}。请用训练时的嵌入配置重新加载。"
            )
        self.classifier = model_data['classifier']
        self.scaler = model_data['scaler']
        self.model_name = model_data['model_name']
        self.training_history = model_data.get('training_history', {})
    
    def plot_results(self, results: Dict, save_path: Optional[str] = None):
        """绘制结果图表"""
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # 混淆矩阵
        conf_matrix = results['confusion_matrix']
        sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['负面', '正面'], yticklabels=['负面', '正面'], ax=axes[0])
        axes[0].set_title('混淆矩阵')
        axes[0].set_xlabel('预测标签')
        axes[0].set_ylabel('真实标签')
        
        # 准确率对比
        metrics = ['精确率', '召回率', 'F1分数']
        negative_scores = [
            results['classification_report']['负面']['precision'],
            results['classification_report']['负面']['recall'],
            results['classification_report']['负面']['f1-score']
        ]
        positive_scores = [
            results['classification_report']['正面']['precision'],
            results['classification_report']['正面']['recall'],
            results['classification_report']['正面']['f1-score']
        ]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        axes[1].bar(x - width/2, negative_scores, width, label='负面', alpha=0.8)
        axes[1].bar(x + width/2, positive_scores, width, label='正面', alpha=0.8)
        
        axes[1].set_xlabel('评估指标')
        axes[1].set_ylabel('分数')
        axes[1].set_title(f"分类指标（整体准确率 {results['accuracy']:.3f}）")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(metrics)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表保存到: {save_path}")
        
        plt.show()


@app.command()
def main(
    input_file: str = typer.Option("data/sentiment_demo.json", help="输入数据文件路径"),
    test_size: float = typer.Option(0.2, help="测试集比例"),
    random_state: int = typer.Option(42, help="随机种子"),
    batch_size: int = typer.Option(32, help="Embedding 生成批次大小"),
    model_path: str = typer.Option("models/dashscope_lr_sentiment.pkl", help="模型保存路径"),
    results_path: str = typer.Option("results/", help="结果保存目录"),
    plot_results: bool = typer.Option(True, help="是否绘制结果图表"),
    regularization: float = typer.Option(1.0, help="逻辑回归 C 参数；固定其他条件比较正则化"),
    feature_cache: Optional[Path] = typer.Option(None, help="保存或复用带数据指纹的 .npz 冻结特征"),
):
    """生成冻结特征，训练分类头，并保存可复核的留出集预测。"""

    # 创建结果目录
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    os.makedirs(results_path, exist_ok=True)
    
    # 先验证数据，再加载模型或读取冻结特征。
    texts, labels = DashScopeSentimentClassifier.load_data(input_file)

    # 初始化分类器
    if feature_cache and feature_cache.suffix != '.npz':
        raise typer.BadParameter("--feature-cache 必须使用 .npz 文件。")
    reused_features = bool(feature_cache and feature_cache.exists())
    cached_model = 'text-embedding-v1'
    if reused_features:
        with np.load(feature_cache, allow_pickle=False) as cached:
            cached_model = str(cached['embedding_model'].item())
        selected = os.getenv('WORKSHOP_LOCAL_EMBEDDING_MODEL')
        if selected and selected != cached_model:
            raise typer.BadParameter("缓存的嵌入模型与当前选择不同，请使用另一个缓存文件。")
    classifier = DashScopeSentimentClassifier(model_name=cached_model, regularization=regularization,
                                             load_encoder=not reused_features)
    
    # 生成 Embedding
    dataset_digest = sha256(json.dumps(list(zip(texts, labels)), ensure_ascii=False).encode()).hexdigest()
    if reused_features:
        with np.load(feature_cache, allow_pickle=False) as cached:
            if str(cached['dataset_sha256'].item()) != dataset_digest:
                raise typer.BadParameter("缓存不属于这份数据及标签，请使用新的缓存路径。")
            embeddings = cached['embeddings']
        if embeddings.ndim != 2 or embeddings.shape[0] != len(texts) or not embeddings.shape[1] or not np.isfinite(embeddings).all():
            raise typer.BadParameter("缓存的特征形状或数值无效。")
        print(f"复用冻结特征：{feature_cache}；本轮不调用嵌入模型。")
    else:
        embeddings = classifier.generate_embeddings(texts, batch_size)
        if feature_cache:
            feature_cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(feature_cache, embeddings=embeddings, dataset_sha256=dataset_digest,
                                embedding_model=classifier.model_name)
            print(f"冻结特征已保存：{feature_cache}")
    
    # 划分数据集
    X_train, X_test, y_train, y_test, _, test_indices = train_test_split(
        embeddings, labels, np.arange(len(texts)),
        test_size=test_size, random_state=random_state, stratify=labels
    )
    
    # 进一步划分训练集和验证集
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=random_state, stratify=y_train
    )
    
    print(f"训练集: {X_train.shape[0]} 样本")
    print(f"验证集: {X_val.shape[0]} 样本")
    print(f"测试集: {X_test.shape[0]} 样本")
    
    # 训练模型
    training_results = classifier.train(X_train, y_train, X_val, y_val)
    
    # 评估模型
    test_results = classifier.evaluate(X_test, y_test)
    
    majority_label = int(np.bincount(y_train).argmax())
    majority_accuracy = float(np.mean(np.asarray(y_test) == majority_label))
    print(f"多数类基线准确率：{majority_accuracy:.4f}；分类头准确率：{test_results['accuracy']:.4f}")
    # 保存模型
    classifier.save_model(model_path)
    
    # 保存结果（转换 numpy 数组为列表）
    results_file = os.path.join(results_path, "classification_results.json")
    
    # 处理 numpy 数组转换
    def convert_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(item) for item in obj]
        else:
            return obj
    
    results_to_save = {
        'test_accuracy': test_results['accuracy'],
        'majority_baseline': {'label': majority_label, 'test_accuracy': majority_accuracy},
        'regularization_C': regularization,
        'dataset_sha256': dataset_digest,
        'features_reused': reused_features,
        'features_sha256': sha256(embeddings.tobytes()).hexdigest(),
        'classification_report': test_results['classification_report'],
        'training_history': convert_numpy(training_results),
        'embedding_model': classifier.model_name,
        'random_state': random_state,
        'test_size': test_size,
        'confusion_matrix': convert_numpy(test_results['confusion_matrix']),
        'test_examples': [
            {
                'source_index': int(index), 'text': texts[index],
                'expected': int(expected), 'predicted': int(predicted),
                'probabilities': probability.tolist(),
            }
            for index, expected, predicted, probability in zip(
                test_indices, y_test, test_results['predictions'], test_results['probabilities']
            )
        ],
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_to_save, f, ensure_ascii=False, indent=2)
    
    print(f"结果保存到: {results_file}")
    
    errors = [row for row in results_to_save['test_examples'] if row['expected'] != row['predicted']]
    print(f"留出集误分类：{len(errors)}/{len(test_indices)}")
    for row in (errors[:3] if errors else results_to_save['test_examples'][:1]):
        print(f"样本 #{row['source_index']}：{row['text']} | 真实={row['expected']}，预测={row['predicted']}")
    # 绘制结果
    if plot_results:
        plot_path = os.path.join(results_path, "classification_results.png")
        classifier.plot_results(test_results, plot_path)
    
    if reused_features:
        print("新文本预测需要重新配置训练时的嵌入模型；本轮比较使用同一留出集。")
        return
    # 演示预测
    demo_texts = [
        "这部电影真的很棒，演员演技出色！",
        "剧情太无聊了，浪费时间。",
        "The movie was absolutely fantastic!",
        "This film is terrible, don't watch it."
    ]
    
    predictions, probabilities = classifier.predict(demo_texts)
    
    print("\n演示预测结果:")
    for text, pred, prob in zip(demo_texts, predictions, probabilities):
        sentiment = "正面" if pred == 1 else "负面"
        confidence = max(prob)
        print(f"文本: {text}")
        print(f"情感: {sentiment} (最大类别概率，未校准: {confidence:.3f})")
        print("-" * 50)


if __name__ == "__main__":
    app()
