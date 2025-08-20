---
layout: default
title: Lesson 5 - RLHF Preference Data Construction
parent: Fine-tuning Data Construction
nav_order: 5
description: "Construct preference pairs for reward modeling"
---

# Lesson 5: RLHF Preference Data Construction
{: .no_toc }

Learn how to construct human feedback preference learning data by generating preference pairs through model comparison methods.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Lesson Information

> **Module**: Chapter 7 - Fine-tuning Data Construction  
> **Prerequisites**: Complete Lessons 1-3  
> **Duration**: 60-90 minutes  
> **Difficulty**: Advanced

---

## Quick Start

```bash
cd chapter7/lesson5
pip install -r requirements.txt
python rlhf_constructor.py --input-file ../lesson3/data/alpaca_data.jsonl --method model_comparison --high-model qwen-plus --low-model qwen-turbo --output-path data/rlhf_pairs.jsonl
```

---

## Next Steps

Proceed to Chapter 8 to learn Fine-tuning Fundamentals.
