---
layout: default
title: Lesson 4 - RLHF Training Data Construction
parent: Fine-tuning Data Construction
nav_order: 4
description: "Construct RLHF preference data for reward modeling and PPO training"
---

# Lesson 4: RLHF Training Data Construction
{: .no_toc }

This lesson demonstrates how to construct RLHF (Reinforcement Learning from Human Feedback) training data. You will learn:
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

- Understand RLHF data requirements and format
- Construct preference data pairs (chosen vs rejected)
- Generate comparison data for reward model training
- Prepare high-quality preference datasets for PPO training

## RLHF Data Characteristics

RLHF requires a special preference data format:
- `prompt`: Input prompt
- `chosen`: Human-preferred answer
- `rejected`: Human-non-preferred answer
- `score_chosen`: Score of preferred answer (optional)
- `score_rejected`: Score of non-preferred answer (optional)

## Feature Overview

- Construct preference pairs from existing conversation data
- Use models to generate multiple candidate answers and rank them
- Automatically construct chosen/rejected comparison data
- Support multiple preference signal sources (scores, rankings, binary choices)
- Output format compliant with RLHF training requirements

## Environment Setup

```bash
cd chapter7/lesson4
pip install -r requirements.txt

# Set API Key for generating candidate answers
export OPENAI_API_KEY="your-openai-key"          # if using OpenAI
export DASHSCOPE_API_KEY="your-dashscope-key"    # if using DashScope
```

## Quick Start

```bash
# Main method: Generate preference pairs using high/low model differences
python rlhf_constructor.py \
  --input-file ../lesson3/data/alpaca_demo.jsonl \
  --method model_comparison \
  --provider dashscope \
  --high-model qwen-max \
  --low-model qwen-plus \
  --output-path data/rlhf_preference.jsonl

# Construct preference pairs from Few-shot data
python rlhf_constructor.py \
  --input-file ../lesson1/data/fewshot_sentiment.jsonl \
  --method model_comparison \
  --provider dashscope \
  --high-model qwen-max \
  --low-model qwen-turbo \
  --output-path data/rlhf_sentiment.jsonl

# Construct preference pairs using OpenAI models
python rlhf_constructor.py \
  --input-file ../lesson2/data/self_instruct.jsonl \
  --method model_comparison \
  --provider openai \
  --high-model gpt-4o \
  --low-model gpt-4o-mini \
  --output-path data/rlhf_openai.jsonl
```

## RLHF Format Examples

### Basic preference pair format
```json
{
  "prompt": "Please explain what machine learning is",
  "chosen": "Machine learning is a branch of artificial intelligence that enables computer systems to automatically learn and improve from data without being explicitly programmed. By analyzing large amounts of data through algorithms, machine learning models can identify patterns, make predictions, and decisions.",
  "rejected": "Machine learning is just a technology that makes machines smart."
}
```

### Format with scores
```json
{
  "prompt": "Please explain what machine learning is",
  "chosen": "Machine learning is a branch of artificial intelligence...",
  "rejected": "Machine learning is just a technology that makes machines smart.",
  "score_chosen": 8.5,
  "score_rejected": 3.2
}
```

## Construction Methods

### 1. model_comparison (Main method)
- **Core idea**: For the same question, generate answers using high-level and low-level models respectively
- **High-level model** (e.g., qwen-max): Generate high-quality answers as `chosen`
- **Low-level model** (e.g., qwen-plus): Generate lower-quality answers as `rejected`
- **Advantage**: Model capability differences naturally ensure quality gradient of preference pairs

### 2. generate_pairs
- Generate multiple candidate answers for each prompt
- Rank answers using quality evaluation models
- Select best and worst answers to form preference pairs

### 3. rank_responses
- Rank existing multiple answers
- Construct preference pairs based on rankings
- Support multiple ranking strategies

## Quality Control

- Automatically filter pairs with insignificant quality differences
- Ensure chosen is significantly better than rejected
- Support manual review and annotation
- Provide data quality analysis reports

## Evaluation Metrics

- Preference pair quality distribution
- chosen/rejected length comparison
- Diversity analysis
- Potential bias detection

## Next Steps

After completing RLHF data construction, you can:
1. Train reward model
2. Use PPO for RLHF training
3. Evaluate model preference alignment effectiveness

## References

- InstructGPT Paper: [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155)
- Anthropic Constitutional AI: [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)
- HuggingFace TRL: [TRL - Transformer Reinforcement Learning](https://github.com/huggingface/trl)

---

## Next Steps

After completing Chapter 7, proceed to [Chapter 8: Fine-Tuning Fundamentals]({{ site.baseurl }}/docs/chapter8).
