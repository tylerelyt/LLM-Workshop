---
layout: default
title: Lesson 1 - Getting Started with Open-Source LLMs
parent: Conversational Intelligence
nav_order: 1
description: "Comprehensive introduction to setting up and using open-source LLMs"
---

# Lesson 1: Getting Started with Open-Source LLMs
{: .no_toc }

This lesson provides a comprehensive introduction to setting up and using open-source Large Language Models (LLMs). Using Llama 3 as a practical example, you will learn how to load a model, perform inference, and integrate it into a simple web service using the `transformers` library.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Key Learning Objectives

- **Model Loading**: Understand how to load any open-source LLM and its tokenizer from the Hugging Face Hub.
- **Text Generation**: Learn the fundamentals of generating text from a given prompt.
- **Agent-based Conversation**: Explore how to build single and multi-agent conversational systems.
- **Flask Integration**: Get hands-on experience wrapping a model in a Flask application to serve it as an API.

---

## File Descriptions

- `prepare_model.py`: A script to download and cache the Llama 3 model, which is used as the example LLM in this lesson.
- `example1.py`: Demonstrates basic text generation with an open-source LLM.
- `example2.py`: Illustrates a simple conversational chat setup.
- `example3.py`: Implements a single-agent chat system.
- `example4.py`: Showcases a more complex multi-agent conversational architecture.
- `common.py`: Contains utility functions for running the Flask web server.
- `agent_a.py`, `agent_b.py`, `agent_c.py`: Define the behaviors and roles of different agents in the multi-agent simulation.
- `requirements.txt`: Lists all the necessary Python dependencies for this lesson.

---

## Setup and Execution

1. **Install Dependencies**:
   Begin by installing the required packages from the `requirements.txt` file.
   ```bash
   pip install -r requirements.txt
   ```

2. **Download the Model**:
   Run the `prepare_model.py` script to fetch the Llama 3 model and tokenizer. This model will be used for the exercises.
   ```bash
   python prepare_model.py
   ```

3. **Run the Examples**:
   You can execute the individual Python scripts to see different functionalities:
   ```bash
   # For basic text generation
   python example1.py

   # To run the multi-agent simulation
   python example4.py
   ```

---

## Next Steps

After completing this lesson, proceed to [Lesson 2: Mathematical Reasoning]({{ site.baseurl }}/docs/chapter1/lesson2).
