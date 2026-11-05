import os
import json
import pickle
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
    """
    GPT-1 Style Fine-tuning: DashScope Embedding + Logistic Regression
    
    This class demonstrates the fundamental principles of GPT-1 fine-tuning:
    1. Use pre-trained embeddings as frozen feature extractors
    2. Train only a simple linear classifier on top
    3. Leverage transfer learning for downstream tasks
    
    This approach mirrors the original GPT-1 methodology before end-to-end
    fine-tuning became the standard practice.
    """
    
    def __init__(self, model_name: str = "text-embedding-v1"):
        """
        初始化分类器
        
        Args:
            model_name: DashScope 模型名称
        """
        self.model_name = model_name
        
        # 初始化 DashScope 客户端
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")
        
        print(f"初始化 DashScope Embedding 客户端: {model_name}")
        self.embedding_client = openai.OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 初始化分类器和预处理器
        self.classifier = LogisticRegression(random_state=42, max_iter=1000)
        self.scaler = StandardScaler()
        
        # 存储训练结果
        self.training_history = {}
        
    def load_data(self, file_path: str) -> Tuple[List[str], List[int]]:
        """加载情感分类数据"""
        print(f"加载数据文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        texts = []
        labels = []
        
        for item in data:
            texts.append(item['sentence'])
            labels.append(item['label'])
        
        print(f"加载了 {len(texts)} 条数据")
        print(f"标签分布: 负面={labels.count(0)}, 正面={labels.count(1)}")
        
        return texts, labels
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 10) -> np.ndarray:
        """
        Generate text embeddings using DashScope API (GPT-1 Style Feature Extraction)
        
        This simulates the frozen pre-trained representation layer in GPT-1 fine-tuning.
        The embeddings are NOT updated during training, only the classifier head is trained.
        """
        print("Generating text embeddings (frozen features)...")
        
        embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="生成 Embedding"):
            batch_texts = texts[i:i + batch_size]
            try:
                # DashScope 支持批量请求
                response = self.embedding_client.embeddings.create(
                    model=self.model_name,
                    input=batch_texts
                )
                batch_embeddings = [np.array(data.embedding) for data in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"生成 Embedding 时出错: {e}")
                # 如果批量失败，尝试单个处理
                for text in batch_texts:
                    try:
                        response = self.embedding_client.embeddings.create(
                            model=self.model_name,
                            input=text
                        )
                        embedding = np.array(response.data[0].embedding)
                        embeddings.append(embedding)
                    except Exception as e2:
                        print(f"处理单个文本时出错: {e2}")
                        # 创建零向量作为fallback
                        embeddings.append(np.zeros(1536))  # DashScope embedding维度
        
        embeddings_array = np.vstack(embeddings)
        print(f"Embedding 维度: {embeddings_array.shape}")
        
        return embeddings_array
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray, y_val: np.ndarray) -> Dict:
        """
        Train the task-specific classifier head (GPT-1 Style Fine-tuning)
        
        This demonstrates the core principle of GPT-1 fine-tuning:
        - Pre-trained embeddings are frozen (no gradient updates)
        - Only the classifier head (logistic regression) is trained
        - This is much faster and requires less data than end-to-end training
        """
        print("Training classifier head (GPT-1 style fine-tuning)...")
        
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
        report = classification_report(y_test, y_pred, target_names=['负面', '正面'], output_dict=True)
        conf_matrix = confusion_matrix(y_test, y_pred)
        
        print(f"测试集准确率: {accuracy:.4f}")
        print("\n分类报告:")
        print(classification_report(y_test, y_pred, target_names=['负面', '正面']))
        
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
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, model_path: str):
        """加载模型"""
        print(f"加载模型从: {model_path}")
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
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
        metrics = ['准确率', '精确率', '召回率', 'F1分数']
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
        
        axes[1].bar(x - width/2, [results['accuracy']] + negative_scores, width, label='负面', alpha=0.8)
        axes[1].bar(x + width/2, [results['accuracy']] + positive_scores, width, label='正面', alpha=0.8)
        
        axes[1].set_xlabel('评估指标')
        axes[1].set_ylabel('分数')
        axes[1].set_title('分类性能对比')
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
):
    """
    GPT-1 Fine-tuning Demonstration: Pre-trained Embeddings + Linear Classifier
    
    This script demonstrates the fundamental principles behind GPT-1 fine-tuning:
    1. Use frozen pre-trained representations (DashScope embeddings)
    2. Train only a simple classifier head (Logistic Regression)
    3. Achieve strong performance with minimal training
    
    This approach was revolutionary in showing that pre-trained language models
    could be effectively adapted to downstream tasks with simple modifications.
    """
    
    # 创建结果目录
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    os.makedirs(results_path, exist_ok=True)
    
    # 初始化分类器
    classifier = DashScopeSentimentClassifier()
    
    # 加载数据
    texts, labels = classifier.load_data(input_file)
    
    # 生成 Embedding
    embeddings = classifier.generate_embeddings(texts, batch_size)
    
    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, labels, test_size=test_size, random_state=random_state, stratify=labels
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
        'classification_report': test_results['classification_report'],
        'training_history': convert_numpy(training_results)
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_to_save, f, ensure_ascii=False, indent=2)
    
    print(f"结果保存到: {results_file}")
    
    # 绘制结果
    if plot_results:
        plot_path = os.path.join(results_path, "classification_results.png")
        classifier.plot_results(test_results, plot_path)
    
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
        print(f"情感: {sentiment} (置信度: {confidence:.3f})")
        print("-" * 50)


if __name__ == "__main__":
    app()
