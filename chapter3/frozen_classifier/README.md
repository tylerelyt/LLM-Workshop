<a id="lesson-1-gpt-1-fine-tuning-principles--embedding-and-logistic-regression"></a>

# 冻结嵌入与线性分类

通过预训练文本表示和任务分类头，研究模型如何适配情感分析。GPT-1 为预训练与任务适配提供历史背景。本练习冻结嵌入，只训练逻辑回归分类器。完成后，用同一留出集的逐条预测说明分类头学到了什么，并从代码与保存文件中指出被更新的参数。

## 工程任务

小数据集上的分类准确率可能很好看，却未必优于简单基线，也不代表嵌入模型被训练过。

在 [dashscope_lr_sentiment.py](dashscope_lr_sentiment.py) 中，固定嵌入来源、数据划分和留出集，只改变 LogisticRegression 的 C 参数。

固定冻结特征与数据划分，只比较 C 参数；检查多数类基线、留出集误分类与实际更新的权重。

## 概念与架构

- **预训练表示**为每段文本提供一个向量。
- **冻结特征**在训练情感分类器时保持固定。
- **任务学习**根据标注样本拟合逻辑回归权重。
- **迁移学习**复用文本表示来完成下游判断。
- **模型评估**对照训练集、验证集与留出集上的预测结果。

```text
Text → Local BGE or DashScope embeddings → Frozen vectors → Logistic regression → Sentiment
```

完整流程包括加载数据、生成向量、划分样本、标准化特征、训练、评估、保存文件和预测新文本。标准化器在训练集特征上拟合，再用于转换验证集和测试集特征。

<a id="environment-setup"></a>

## 环境准备

使用 Python 3.11 或 3.12，在仓库根目录安装本课依赖。

```bash
python -m pip install -r chapter3/frozen_classifier/requirements.txt
```

选择本次实验的嵌入来源。本地路径会在首次运行时下载模型。

```bash
export WORKSHOP_LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

使用 DashScope 的 `text-embedding-v1` 时，取消 `WORKSHOP_LOCAL_EMBEDDING_MODEL` 环境变量，并在终端配置 `DASHSCOPE_API_KEY`。加载已保存的分类器做预测时，使用与训练时相同的嵌入来源。

<a id="quick-start"></a>

## 快速开始

从仓库根目录运行提供的情感数据集。命令通过子 shell 进入课时目录，以便使用相对的数据路径和输出路径。

```bash
(cd chapter3/frozen_classifier && python dashscope_lr_sentiment.py \
  --input-file data/sentiment_demo.json --batch-size 5)
```

程序会打印各类别数量、训练集/验证集/测试集大小、评价指标和预测示例，并打开图表。需要保存评价数据而不打开图表时，使用布尔选项 `--no-plot-results`。

```bash
(cd chapter3/frozen_classifier && python dashscope_lr_sentiment.py \
  --input-file data/sentiment_demo.json \
  --test-size 0.2 --random-state 42 --batch-size 5 \
  --model-path models/my_sentiment_model.pkl \
  --results-path results/my_experiment --no-plot-results)
```

<a id="parameters"></a>

## 固定特征，比较分类头

给同一数据集准备一个本轮专用的特征缓存，第一次运行生成特征，第二次只改变 C。两轮使用相同的划分种子、数据和缓存，将模型与结果保存到不同路径。

```bash
CLASSIFIER_RUN=$(mktemp -d)
python chapter3/frozen_classifier/dashscope_lr_sentiment.py \
  --input-file chapter3/frozen_classifier/data/sentiment_demo.json \
  --feature-cache "$CLASSIFIER_RUN/features.npz" --regularization 0.1 \
  --model-path "$CLASSIFIER_RUN/c01.pkl" --results-path "$CLASSIFIER_RUN/c01" --no-plot-results
python chapter3/frozen_classifier/dashscope_lr_sentiment.py \
  --input-file chapter3/frozen_classifier/data/sentiment_demo.json \
  --feature-cache "$CLASSIFIER_RUN/features.npz" --regularization 2 \
  --model-path "$CLASSIFIER_RUN/c2.pkl" --results-path "$CLASSIFIER_RUN/c2" --no-plot-results
```

沿用上面的嵌入配置。第二轮读取已保存的特征，不调用嵌入模型，也不生成新的文本预测。程序会核对缓存中的数据与标签指纹；更换数据或明确选择不同嵌入来源时应使用新缓存。

对照两份结果中的 `dataset_sha256`、`features_sha256` 与留出样本索引，确认比较基础一致。再看多数类基线、分类指标及误分类原文，解释 C 的变化是否有实际收益。不要根据训练集准确率或少量自拟例子选型，也不要反复用同一留出集调参后仍把它当成未见测试；进一步选型时在验证集上比较，再使用新的独立测试集。

## 参数说明

| 选项 | 含义 | 默认值 |
|---|---|---|
| `--input-file` | JSON 数据集路径 | `data/sentiment_demo.json` |
| `--test-size` | 留作测试集的样本比例 | `0.2` |
| `--random-state` | 划分数据集的随机种子 | `42` |
| `--batch-size` | 每个嵌入批次的文本数量 | `32` |
| `--model-path` | 分类器文件路径 | `models/dashscope_lr_sentiment.pkl` |
| `--results-path` | 评价结果输出目录 | `results/` |
| `--plot-results` / `--no-plot-results` | 保存并显示评价图表 | 开启 |

<a id="input-data"></a>

## 输入数据

每条 JSON 记录包含 `sentence` 和二分类 `label`，其中 `1` 表示正面情感，`0` 表示负面情感。

```json
[
  {"sentence": "This movie is really great!", "label": 1},
  {"sentence": "The plot is too boring.", "label": 0},
  {"sentence": "The movie was fantastic!", "label": 1},
  {"sentence": "This film is terrible.", "label": 0}
]
```

运行示例时使用提供的完整数据集。自定义数据集需要为每个类别准备足够的样本，以便分层划分训练集、验证集和测试集。比较指标前，先检查类别数量和标签是否一致。

<a id="output-artifacts-and-metrics"></a>

## 输出文件与评价指标

| 文件或输出 | 内容 |
|---|---|
| `models/dashscope_lr_sentiment.pkl` | 分类器、标准化器、嵌入模型名称和训练记录 |
| `results/classification_results.json` | 测试集准确率、分类报告、训练记录、嵌入来源、划分设置、混淆矩阵与逐条 `test_examples` |
| `results/classification_results.png` | 开启绘图时生成的混淆矩阵和指标对比图 |
| 终端输出 | 数据集划分大小、训练集/验证集/测试集结果和新文本预测 |

结合留出集中的实际样本解读各项指标。

| 指标 | 回答的问题 |
|---|---|
| 准确率（Accuracy） | 预测结果中有多大比例与标签一致？ |
| 精确率（Precision） | 被预测为某个类别的样本中，有多大比例确实属于该类别？ |
| 召回率（Recall） | 属于某个类别的样本中，有多大比例被找到了？ |
| F1 | 该类别的精确率与召回率综合表现如何？ |

小数据集中，少量样本就可能让指标明显变化。比较运行结果时，记录随机种子、数据集划分大小和被错误分类的文本。

<a id="inspect-the-python-api"></a>

## 检查 Python API

选择嵌入来源后，在 `chapter3/frozen_classifier` 目录启动 Python。下面的示例沿用命令行程序中的特征生成、数据划分、训练和评估步骤。

```python
from pathlib import Path
from sklearn.model_selection import train_test_split
from dashscope_lr_sentiment import DashScopeSentimentClassifier

classifier = DashScopeSentimentClassifier()
texts, labels = classifier.load_data("data/sentiment_demo.json")
features = classifier.generate_embeddings(texts)
X_dev, X_test, y_dev, y_test = train_test_split(
    features, labels, test_size=0.2, random_state=42, stratify=labels
)
X_train, X_val, y_train, y_val = train_test_split(
    X_dev, y_dev, test_size=0.2, random_state=42, stratify=y_dev
)
classifier.train(X_train, y_train, X_val, y_val)
metrics = classifier.evaluate(X_test, y_test)
print(metrics["accuracy"], metrics["confusion_matrix"])
Path("models").mkdir(exist_ok=True)
classifier.save_model("models/my_sentiment_model.pkl")
```

<a id="predict-new-text"></a>

### 预测新文本

使用上一个示例中训练好的分类器。

```python
texts = ["This movie is really great!", "The plot is too boring"]
predictions, probabilities = classifier.predict(texts)
for text, prediction, probability in zip(texts, predictions, probabilities):
    sentiment = "Positive" if prediction == 1 else "Negative"
    print(f"{text} -> {sentiment} ({max(probability):.3f})")
```

<a id="load-the-saved-classifier"></a>

### 加载已保存的分类器

启动另一个 Python 会话，并使用与训练时相同的嵌入配置。

```python
from dashscope_lr_sentiment import DashScopeSentimentClassifier

classifier = DashScopeSentimentClassifier()
classifier.load_model("models/my_sentiment_model.pkl")
predictions, probabilities = classifier.predict(["This movie is really great!"])
print(predictions, probabilities)
```

<a id="practice-and-acceptance"></a>

## 练习与验收

先按快速开始运行基线，保留 `classification_results.json`。在 `test_examples` 中逐条对照原文、`expected`、`predicted` 与概率，选一条预测错误或最不确定的样本，解释其用词与标签。将逐条计数与混淆矩阵、准确率对应起来。

然后通过 `--regularization 0.1` 改变分类头的 C 参数。固定输入文件、嵌入来源、`--random-state 42`、测试集比例与特征缓存，将模型和结果写入新的路径。比较两份 JSON 的 `test_examples.source_index`，确认留出集没有变化，再对照同一文本的预测与概率。没有出现准确率提升也是有效观察，需要解释这次正则化变化实际影响了哪些结果。

重新加载其中一份分类器，对相同文本重做预测，核对结果一致。保存文件中的 `classifier.coef_` 和 `scaler` 来自本轮分类任务拟合；嵌入模型的参数由所选来源提供并保持固定。加载不同嵌入来源训练的分类器时，程序会要求恢复训练配置，避免把不匹配的特征传给分类头。

对照基线与修改后同一条留出样本的记录、两份指标和重载预测结果，说明本次训练更新了哪些参数。这个证据覆盖冻结表示上的线性分类，后续 Transformer 梯度更新需要另设训练与验证实验。每轮使用独立输出路径，复跑基线时使用原来的 C 参数。

冻结特征让任务学习的检查成本较低，线性分类头则呈现简单的决策边界。后续可以尝试 SVM 或树模型、多分类标签、Transformer 全参数梯度更新，以及 LoRA、QLoRA 等参数高效方法。比较不同方法时，使用同一数据集和评价规则。

规划更大规模的适配实验时，复核LLM 基础中的指令数据与偏好数据。[LLM 基础](../../chapter5/README.md) · [主题目录](../README.md) · [课程概览](../../README.md)

## 在自己的项目中使用

选择一个有明确二分类标签的实际任务，检查类别分布、重复记录和标签歧义，再用同一划分建立简单基线与分类头结果。若错误集中在少数输入类型，先补查数据覆盖，再决定是否更换表示。结合[指令数据](../../chapter5/fewshot_data/README.md)，区分用于训练、运行时示例与最终测试的样本。
