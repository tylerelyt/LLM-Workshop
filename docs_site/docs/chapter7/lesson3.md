---
layout: default
title: Lesson 3 - Alpaca Training Data Construction
parent: Fine-tuning Data Construction
nav_order: 3
description: "Construct Alpaca-style training data for supervised fine-tuning"
---

# Lesson 3: Alpaca Training Data Construction
{: .no_toc }

This lesson demonstrates how to construct Alpaca-style training data, the standard format used by the Stanford Alpaca project. You will learn:
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

- Understand the standardized structure of Alpaca data format
- Convert from various source data formats to Alpaca format
- Construct dialogue data suitable for supervised fine-tuning (SFT)
- Prepare high-quality training sets for instruction fine-tuning

## Alpaca Format Characteristics

Alpaca format is the classic format for instruction fine-tuning, containing three fields:
- `instruction`: Task instruction
- `input`: Optional input context
- `output`: Expected output

## Feature Overview

- Support multiple source data formats converted to Alpaca standard format
- Built-in Alpaca-style instruction template library
- Automatically handle cases with/without input
- Support batch data conversion and quality filtering
- Output standard JSONL format, directly usable for training

## Environment Setup

```bash
cd chapter7/lesson3
pip install -r requirements.txt
```

## Quick Start

```bash
# Method 1: Convert from Few-shot data to Alpaca format
python alpaca_constructor.py \
  --input-file ../lesson1/data/fewshot_sentiment.jsonl \
  --output-path data/alpaca_sentiment.jsonl \
  --conversion-type fewshot_to_alpaca

# Method 2: Construct Alpaca format from Q&A pairs
python alpaca_constructor.py \
  --input-file data/qa_pairs.json \
  --output-path data/alpaca_qa.jsonl \
  --conversion-type qa_to_alpaca

# Method 3: Construct Alpaca format from conversation data
python alpaca_constructor.py \
  --input-file data/conversations.jsonl \
  --output-path data/alpaca_chat.jsonl \
  --conversion-type chat_to_alpaca
```

## Alpaca Format Examples

### Example without input
```json
{
  "instruction": "Explain what machine learning is",
  "input": "",
  "output": "Machine learning is a branch of artificial intelligence that enables computer systems to automatically learn and improve from data without being explicitly programmed..."
}
```

### Example with input
```json
{
  "instruction": "Translate the following text to English",
  "input": "Artificial intelligence is changing our world",
  "output": "Artificial intelligence is changing our world"
}
```

## Conversion Types

- `fewshot_to_alpaca`: Convert Few-shot instructions to concise Alpaca format
- `qa_to_alpaca`: Convert Q&A pairs to Alpaca format
- `chat_to_alpaca`: Convert conversation data to Alpaca format
- `classification_to_alpaca`: Convert classification data to Alpaca format

## Data Quality Control

- Automatically filter instructions/answers that are too short or too long
- Deduplicate instructions to maintain dataset diversity
- Standardize format to ensure training compatibility
- Support manual review and batch editing

## Next Steps

After completing Alpaca data construction, you can:
1. Directly use for LoRA or full parameter fine-tuning
2. Proceed to `chapter7/lesson4` to construct RLHF training data
3. Mix with other datasets to increase training diversity

## References

- Stanford Alpaca Project: [tatsu-lab/stanford_alpaca](https://github.com/tatsu-lab/stanford_alpaca)
- Alpaca Dataset: [yahma/alpaca-cleaned](https://huggingface.co/datasets/yahma/alpaca-cleaned)

---

## Next Steps

After completing this lesson, proceed to [Lesson 4: RLHF Preference Data Construction]({{ site.baseurl }}/docs/chapter7/lesson4).
