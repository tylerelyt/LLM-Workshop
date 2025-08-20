---
layout: default
title: Lesson 2 - Advanced LLM Applications
parent: Conversational Intelligence
nav_order: 2
description: "Agent-based systems, RAG, and chain-of-thought prompting"
---

# Lesson 2: Advanced LLM Applications
{: .no_toc }

This lesson explores advanced applications of Large Language Models, focusing on agent-based systems, retrieval-augmented generation (RAG), and chain-of-thought prompting. You will learn how to build sophisticated applications that leverage external tools, document retrieval, and complex reasoning.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Key Learning Objectives

- **Agent Creation**: Learn to create agents with custom tools using LangChain.
- **Code Translation**: Use an LLM for programmatic code translation between languages.
- **Retrieval-Augmented Generation (RAG)**: Build a RAG pipeline to answer questions from a knowledge base.
- **Chain of Thought**: Implement sequential chains for complex, multi-step problem-solving.
- **Document Analysis**: Apply an LLM to analyze and answer questions about a legal document.

---

## File Descriptions

- `example1.py`: Demonstrates how to build a LangChain agent with a custom tool for mathematical calculations.
- `example2.py`: Shows how to use Ollama for code translation from Python to JavaScript.
- `example3.py`: Implements a RAG system using ChromaDB for vector storage and `bge-m3` for embeddings.
- `example4.py`: Illustrates a sequential chain-of-thought process for structured problem-solving.
- `example5.py`: Provides an example of document analysis on a legal text.
- `data/legal_document.txt`: A sample legal document used in `example5.py`.
- `requirements.txt`: Lists all the necessary Python dependencies for this lesson.

---

## Setup and Execution

1. **Install Dependencies**:
   Install the required packages using pip.
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Examples**:
   Execute the individual scripts to explore the different functionalities.
   ```bash
   # For the custom tool agent
   python example1.py

   # For the RAG system
   python example3.py

   # For the document analysis
   python example5.py
   ```

---

## Next Steps

After completing this lesson, proceed to [Lesson 3: Building a Tool-Using Agent]({{ site.baseurl }}/docs/chapter1/lesson3).
