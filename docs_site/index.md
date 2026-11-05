---
layout: default
title: Home
nav_order: 1
description: "Enterprise-grade Large Language Model Application Development - End-to-end engineering practices from dialog systems to multimodal applications"
permalink: /
---

# LLM-Workshop
{: .fs-9 }

A hands-on workshop bridging industry, academia, and research. Master cutting-edge LLM technologies through **Learning-by-Doing** - build real systems, understand core principles, and accelerate from concept to production.
{: .fs-6 .fw-300 }

[Quick Start](#-quick-start){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[GitHub Repository](https://github.com/tylerelyt/LLM-Workshop){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## Workshop Philosophy
{: .text-delta }

**LLM-Workshop** is a **practical workshop**, not a traditional course. We believe in **Learning-by-Doing** - the fastest path to mastering cutting-edge technology is through hands-on implementation.

### Core Principles

- **🔬 Research-Driven**: Each module is grounded in latest academic papers and industry research
- **🏭 Industry-Proven**: Architecture patterns reflect real-world practices from leading AI companies
- **🎓 Academic Rigor**: Deep understanding of core principles, not just surface-level implementation
- **⚡ Rapid Mastery**: Focus on essential concepts that unlock understanding of cutting-edge technologies

{: .note }
> **Workshop vs. Course**: We don't teach step-by-step. Instead, we provide working systems and guide you to discover the core principles through hands-on experimentation. Mistakes are not failures—they're insights.

### Industry-Academia-Research Integration

This workshop synthesizes insights from three domains:

- **📚 Academic Research**: Latest papers translated into working code
- **🏢 Industry Practices**: Production-grade patterns from real deployments
- **🔬 Research Innovation**: Experimental features and cutting-edge techniques

**Result**: You gain both theoretical depth and practical expertise, enabling rapid adoption of new technologies as they emerge.

### Cutting-Edge Technology Focus

Master the **core essence** of technologies that matter:

- 🧠 **Conversational Intelligence**: Long-context processing and reasoning frameworks
- 🔍 **Knowledge Engineering**: RAG systems and knowledge graph construction
- 🤖 **Multi-Agent**: Distributed AI coordination and task orchestration
- 🎨 **Multimodal**: Image-text processing and cross-modal understanding
- ⚙️ **Fine-Tuning Engineering**: Complete data construction to model training workflow

---

## Platform Overview
{: .text-delta }

**Full-Stack AI Systems** covering eight core areas:

🧠 **Conversational Intelligence**
{: .label .label-blue }
Basic dialogs, instruction following, tool-augmented agents
{: .fs-3 }

🔬 **Advanced Reasoning**
{: .label .label-green }
Chain-of-thought, zero-shot reasoning, tree-of-thought exploration
{: .fs-3 }

🔍 **Retrieval & Knowledge Engineering**
{: .label .label-purple }
Production-grade RAG, knowledge graph construction, NL2SQL
{: .fs-3 }

🧠 **Context Engineering**
{: .label .label-yellow }
KV-Cache optimization, tool masking, externalized memory
{: .fs-3 }

🎨 **Multimodal Models**
{: .label .label-red }
Image recognition, document processing, multimodal understanding
{: .fs-3 }

🤖 **Multi-Agent Orchestration**
{: .label .label-blue }
Function calling, code interpreters, reflection systems
{: .fs-3 }

🧪 **Fine-Tuning Data Construction**
{: .label .label-green }
Few-shot, Self-Instruct, Alpaca, RLHF
{: .fs-3 }

⚡ **Fine-Tuning Fundamentals**
{: .label .label-purple }
GPT-1 style fine-tuning, feature transfer learning
{: .fs-3 }

---

## 🚀 Quick Start
{: .text-delta }

### Environment Setup

```bash
# Clone repository
git clone https://github.com/tylerelyt/LLM-Workshop.git
cd LLM-Workshop

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Configure API keys
export DASHSCOPE_API_KEY="your-dashscope-key"
export OPENAI_API_KEY="your-openai-key"  # Optional
```

### Install Dependencies

```bash
# Install dependencies for specific chapters as needed
# Chapter 1: Conversational Intelligence
pip install -r chapter1/lesson1/requirements.txt

# Chapter 3: Retrieval & Knowledge Engineering
pip install -r chapter3/lesson1/requirements.txt
pip install -r chapter3/lesson2/requirements.txt
pip install -r chapter3/lesson3/requirements.txt

# Chapter 6: Multi-Agent Orchestration
pip install -r chapter6/lesson1/requirements.txt
pip install -r chapter6/lesson2/requirements.txt
```

### Run Examples

```bash
# Build interactive knowledge graph
cd chapter3/lesson2
python knowledge_pipeline.py

# Create production-grade RAG system
cd chapter3/lesson1
python rag_pipeline.py

# Develop enterprise-grade NL2SQL system
cd chapter3/lesson3
python nl2sql_engine.py

# Build multi-agent system
cd chapter6/lesson1
python function_call_workshop.py
```

{: .note }
> After system startup, follow the instructions in the terminal output for interactive operations.

---

## 📚 Documentation Navigation
{: .text-delta }

<div class="code-example" markdown="1">

### Core Modules

[Conversational Intelligence]({{ site.baseurl }}/docs/chapter1){: .btn .btn-outline }
- [Agent Architecture]({{ site.baseurl }}/docs/chapter1/lesson1)
- [Mathematical Reasoning]({{ site.baseurl }}/docs/chapter1/lesson2)
- [Multimodal Dialog]({{ site.baseurl }}/docs/chapter1/lesson3)
- [Tool Augmentation]({{ site.baseurl }}/docs/chapter1/lesson4)
- [In-Context Learning]({{ site.baseurl }}/docs/chapter1/lesson5)

[Advanced Reasoning]({{ site.baseurl }}/docs/chapter2){: .btn .btn-outline }
- [Chain-of-Thought]({{ site.baseurl }}/docs/chapter2/lesson1)
- [Zero-Shot Reasoning]({{ site.baseurl }}/docs/chapter2/lesson2)
- [Tree of Thoughts]({{ site.baseurl }}/docs/chapter2/lesson3)

[Retrieval & Knowledge Engineering]({{ site.baseurl }}/docs/chapter3){: .btn .btn-outline }
- [RAG System]({{ site.baseurl }}/docs/chapter3/lesson1)
- [Knowledge Graph]({{ site.baseurl }}/docs/chapter3/lesson2)
- [NL2SQL]({{ site.baseurl }}/docs/chapter3/lesson3)

[Context Engineering]({{ site.baseurl }}/docs/chapter4){: .btn .btn-outline }
- [KV-Cache Optimization]({{ site.baseurl }}/docs/chapter4/lesson1)
- [Tool Masking Strategy]({{ site.baseurl }}/docs/chapter4/lesson2)
- [Filesystem Memory]({{ site.baseurl }}/docs/chapter4/lesson3)
- [Attention Recitation]({{ site.baseurl }}/docs/chapter4/lesson4)
- [Error Preservation]({{ site.baseurl }}/docs/chapter4/lesson5)

[Multimodal Models]({{ site.baseurl }}/docs/chapter5){: .btn .btn-outline }
- [Image Content Analysis]({{ site.baseurl }}/docs/chapter5/lesson1)
- [Document Processing]({{ site.baseurl }}/docs/chapter5/lesson2)

[Multi-Agent Orchestration]({{ site.baseurl }}/docs/chapter6){: .btn .btn-outline }
- [Manual Function Calling]({{ site.baseurl }}/docs/chapter6/lesson1)
- [AutoGen Function Calling]({{ site.baseurl }}/docs/chapter6/lesson2)
- [Code Interpreter]({{ site.baseurl }}/docs/chapter6/lesson3)
- [Reflection System]({{ site.baseurl }}/docs/chapter6/lesson4)
- [MemGPT Integration]({{ site.baseurl }}/docs/chapter6/lesson5)

[Fine-Tuning Data Construction]({{ site.baseurl }}/docs/chapter7){: .btn .btn-outline }
- [Few-shot Data]({{ site.baseurl }}/docs/chapter7/lesson1)
- [Self-Instruct]({{ site.baseurl }}/docs/chapter7/lesson2)
- [Alpaca Format]({{ site.baseurl }}/docs/chapter7/lesson3)
- [RLHF Preference Data]({{ site.baseurl }}/docs/chapter7/lesson4)

[Fine-Tuning Fundamentals]({{ site.baseurl }}/docs/chapter8){: .btn .btn-outline }
- [GPT-1 Style Fine-Tuning]({{ site.baseurl }}/docs/chapter8/lesson1)

</div>

---

## 🛠️ Technology Stack
{: .text-delta }

| Category | Technologies |
|:---------|:------------|
| **Large Language Models** | DashScope (Qwen), OpenAI API, Ollama |
| **Vector Retrieval** | BGE-M3, BGE-reranker, FlagEmbedding |
| **Knowledge Graphs** | NetworkX, Pyvis, Neo4j |
| **Multimodal** | Qwen-VL-Max, CLIP, LayoutParser |
| **Agent Frameworks** | AutoGen, LangChain, ReAct |
| **Fine-Tuning Tools** | LLaMA-Factory, LoRA, RLHF |
| **Data Processing** | Pandas, NumPy, scikit-learn |

---

## 🌟 Workshop Features

- ✅ **Working Systems**: Complete, runnable code for every module - not toy examples
- ✅ **Research Integration**: Latest academic papers implemented as working systems
- ✅ **Industry Patterns**: Real-world architectural patterns from production deployments
- ✅ **Core Principle Focus**: Understand the essence, not just the implementation
- ✅ **Rapid Experimentation**: Modify, break, and learn through hands-on exploration

---

## 🎯 Who Should Attend This Workshop?
{: .text-delta }

This workshop is designed for practitioners who learn by **doing**, not just reading:

- **🔬 Research Engineers** - Translate cutting-edge papers into working systems
- **🏭 Industry Practitioners** - Rapidly adopt new technologies for production use
- **🎓 Academic Researchers** - Bridge theory and practice, understand implementation details
- **🚀 Technology Leaders** - Master core principles to evaluate and integrate new technologies

{: .note }
> **Learning-by-Doing Philosophy**: Each module provides a working system. Your task is to experiment, break things, understand why they work, and discover the core principles. This is how you truly master cutting-edge technology.

---

## 📖 Workshop Paths
{: .text-delta }

Choose your path based on your goals. Each path emphasizes **hands-on experimentation** to discover core principles:

### 🚀 Quick Start Path: Core Concepts
**Goal**: Rapidly understand essential LLM capabilities

1. Chapter 1: Conversational Intelligence (Lesson 1-2) - Build your first agent
2. Chapter 2: Advanced Reasoning (Lesson 1) - Master chain-of-thought
3. Chapter 4: Context Engineering (Lesson 1-2) - Optimize for production

**Time**: 2-3 hours of hands-on work

### 🔬 Research Path: Deep Understanding
**Goal**: Master cutting-edge research and translate papers to code

1. Chapter 3: Retrieval & Knowledge Engineering (All) - Production RAG systems
2. Chapter 5: Multimodal Models (Lesson 1) - Vision-language integration
3. Chapter 6: Multi-Agent Orchestration (Lesson 1-2) - Advanced agent patterns

**Time**: 4-6 hours of experimentation

### 🏭 Production Path: Enterprise Systems
**Goal**: Build production-ready systems with industry patterns

1. Chapter 6: Multi-Agent Orchestration (All) - Complete agent frameworks
2. Chapter 7: Fine-Tuning Data Construction (All) - Data pipelines
3. Chapter 8: Fine-Tuning Fundamentals (All) - Model customization

**Time**: 6-8 hours of implementation

{: .note }
> **Workshop Approach**: Don't just follow tutorials. Run the code, modify it, break it, fix it. This is how you discover the core principles that enable rapid adoption of new technologies.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](https://github.com/tylerelyt/LLM-Workshop/blob/main/LICENSE) file for details. You are free to use, modify, and distribute this code, including for commercial purposes.

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. **Fork** this repository
2. **Create** a feature branch (`git checkout -b feature-amazing`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature-amazing`)
5. **Submit** a Pull Request

## 📞 Contact

- **Project Homepage**: [https://github.com/tylerelyt/LLM-Workshop](https://github.com/tylerelyt/LLM-Workshop)
- **Issue Tracker**: [https://github.com/tylerelyt/LLM-Workshop/issues](https://github.com/tylerelyt/LLM-Workshop/issues)

---

