---
layout: default
title: Lesson 2 - Improving Reliability with Self-Consistency
parent: Advanced Reasoning
nav_order: 2
description: "Self-Consistency technique for improved reliability"
---

# Lesson 2: Improving Reliability with Self-Consistency
{: .no_toc }

This lesson introduces Self-Consistency, an advanced technique to improve the reliability of an LLM's responses, particularly for tasks that involve reasoning and calculation.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Key Learning Objectives

- **Understanding Self-Consistency**: Learn the core concept of Self-Consistency, which involves generating multiple responses to a single prompt and choosing the most frequent answer.
- **Implementation**: See how to implement a Self-Consistency workflow by repeatedly calling an LLM and aggregating the results.
- **Answer Extraction**: Learn how to parse the model's output to extract the final answer, even when the response includes a chain of reasoning.

---

## File Descriptions

- `example1.py`: Demonstrates the Self-Consistency technique by posing a multi-step math problem to the LLM. It generates several answers, extracts the final numerical result from each one, and selects the most common result as the definitive answer.
- `requirements.txt`: Lists all the necessary Python dependencies for this lesson.

---

## Setup and Execution

1. **Install Dependencies**:
   Install the required packages using pip.
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Example**:
   Execute the script to see the Self-Consistency process in action.
   ```bash
   python example1.py
   ```
   The script will print each of the generated reasoning paths and then display the final, most consistent answer.

---

## Next Steps

After completing this lesson, proceed to [Lesson 3: Tree of Thoughts]({{ site.baseurl }}/docs/chapter2/lesson3).
