---
layout: default
title: Lesson 1 - GPT-1 Fine-tuning Principles
parent: Fine-tuning Fundamentals
nav_order: 1
description: "GPT-1 style fine-tuning with frozen embeddings and linear classifier"
---

# Chapter 8 Lesson 1: GPT-1 Fine-tuning Principles - Embedding + Logistic Regression
{: .no_toc }

This lesson demonstrates the fundamental principles behind GPT-1 fine-tuning by using pre-trained embeddings (DashScope) combined with a simple classifier (Logistic Regression) for sentiment analysis. This approach mirrors the original GPT-1 methodology of leveraging pre-trained representations for downstream tasks.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## GPT-1 Fine-tuning Concepts

This implementation demonstrates key concepts from the original GPT-1 paper:

- **Pre-trained Representations**: Uses DashScope embeddings as frozen feature extractors (similar to GPT-1's pre-trained transformer)
- **Task-specific Head**: Logistic regression serves as the classification head for sentiment analysis
- **Transfer Learning**: Leverages general language understanding for specific downstream tasks
- **Feature-based Approach**: Shows the foundation before end-to-end fine-tuning became standard

## Features

- **Pre-trained Embeddings**: DashScope text-embedding-v1 as the feature extractor
- **Linear Classifier**: Logistic regression as the task-specific head
- **Multilingual Support**: Chinese-English mixed text processing
- **Complete Pipeline**: Training, evaluation, and inference workflow
- **Educational Focus**: Clear demonstration of early fine-tuning principles

## Technical Architecture (GPT-1 Style)

```
Text Input → Pre-trained Embeddings → [FROZEN] → Linear Classifier → Task Output
            (DashScope API)                        (Logistic Regression)   (Sentiment)
```

## Environment Setup

```bash
cd chapter8/lesson1
pip install -r requirements.txt

# Set API Key
export DASHSCOPE_API_KEY="your-dashscope-api-key"
```

## Quick Start

```bash
# Basic demo
python dashscope_lr_sentiment.py

# Custom parameters
python dashscope_lr_sentiment.py \
  --input-file data/sentiment_demo.json \
  --test-size 0.2 \
  --batch-size 5 \
  --model-path models/my_sentiment_model.pkl
```

## Parameters

- `--input-file`: Input data file path (JSON format)
- `--test-size`: Test set ratio, default 0.2
- `--random-state`: Random seed, default 42
- `--batch-size`: Embedding generation batch size, default 32
- `--model-path`: Model save path, default models/dashscope_lr_sentiment.pkl
- `--results-path`: Results save directory, default results/
- `--plot-results`: Whether to plot results charts, default True

## Input Data Format

JSON format with sentence and label fields:

```json
[
  {"sentence": "This movie is really great!", "label": 1},
  {"sentence": "The plot is too boring.", "label": 0},
  {"sentence": "The movie was fantastic!", "label": 1},
  {"sentence": "This film is terrible.", "label": 0}
]
```

## Output Results

### 1. Model Files
- `models/dashscope_lr_sentiment.pkl`: Trained model

### 2. Evaluation Results
- `results/classification_results.json`: Detailed classification report
- `results/classification_results.png`: Visualization charts

### 3. Console Output
- Training process information
- Accuracy, precision, recall, F1-score metrics
- Demo prediction results

## Performance Metrics

The model outputs the following performance metrics:
- **Accuracy**: Overall classification accuracy
- **Precision**: Proportion of true positives among predicted positives
- **Recall**: Proportion of true positives among actual positives
- **F1-score**: Harmonic mean of precision and recall

## Usage Examples

### Training Model
```python
from dashscope_lr_sentiment import DashScopeSentimentClassifier

# Initialize classifier
classifier = DashScopeSentimentClassifier()

# Load data
texts, labels = classifier.load_data("data/sentiment_demo.json")

# Generate embeddings
embeddings = classifier.generate_embeddings(texts)

# Train model
# ... (automatic data splitting and training)
```

### Predicting New Text
```python
# Predict single text
texts = ["This movie is really great!", "The plot is too boring"]
predictions, probabilities = classifier.predict(texts)

for text, pred, prob in zip(texts, predictions, probabilities):
    sentiment = "Positive" if pred == 1 else "Negative"
    confidence = max(prob)
    print(f"{text} -> {sentiment} ({confidence:.3f})")
```

### Loading Trained Model
```python
# Load model
classifier = DashScopeSentimentClassifier()
classifier.load_model("models/dashscope_lr_sentiment.pkl")

# Direct prediction
predictions, probabilities = classifier.predict(["New text"])
```

## Educational Value (GPT-1 Principles)

1. **Historical Significance**: Demonstrates the foundational approach that led to modern fine-tuning
2. **Conceptual Clarity**: Separates feature extraction from task-specific learning
3. **Efficiency**: Shows how frozen embeddings can be effective for many tasks
4. **Interpretability**: Linear head makes decision boundaries more interpretable
5. **Foundation Knowledge**: Essential understanding before exploring end-to-end fine-tuning

## Notes

- Requires DASHSCOPE_API_KEY environment variable
- API calls incur costs, please control batch sizes
- May need parameter tuning for small datasets
- Logistic regression works best for linearly separable data

## Extensions & Next Steps

- **Other Classifiers**: Replace logistic regression with SVM, Random Forest, etc.
- **Multi-class Tasks**: Extend to multi-class classification problems
- **End-to-end Fine-tuning**: Progress to full transformer fine-tuning (GPT-2+ style)
- **Modern Approaches**: Compare with recent fine-tuning methods (LoRA, QLoRA, etc.)
- **Production Deployment**: Scale to larger datasets and real applications

## Learning Path

1. **Start Here**: Understand feature-based fine-tuning (this lesson)
2. **Next**: Explore full transformer fine-tuning with gradient updates
3. **Advanced**: Study parameter-efficient fine-tuning methods
4. **Modern**: Learn about instruction tuning and RLHF

---

## Next Steps

Congratulations! You have completed all chapters of the LLM-Workshop. Continue exploring advanced topics and building production-ready AI systems.

