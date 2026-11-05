# LLM-Workshop

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/tylerelyt/LLM-Workshop.svg?style=social&label=Star)](https://github.com/tylerelyt/LLM-Workshop)
[![GitHub forks](https://img.shields.io/github/forks/tylerelyt/LLM-Workshop.svg?style=social&label=Fork)](https://github.com/tylerelyt/LLM-Workshop)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

> **Learn Large Language Model development through hands-on projects and real-world implementations.**

A practical workshop for building LLM applications from scratch. Learn by doing - each project guides you through essential concepts while building production-ready systems, from conversational AI to multimodal applications.

## 🏗️ Workshop Structure

**LLM-Workshop** provides hands-on learning experiences through practical projects, featuring:

- **🧠 Conversational AI** - Advanced dialog systems with reasoning capabilities
- **🔍 Retrieval-Augmented Generation** - Knowledge-grounded QA systems and vector databases
- **🕸️ Knowledge Graph Engineering** - Automated entity extraction and graph visualization
- **🤖 Multi-Agent Systems** - Distributed AI coordination and task orchestration
- **🎨 Multimodal Models** - Image, text and document processing with advanced vision-language models
- **⚡ Production Infrastructure** - Scalable deployment patterns and monitoring

## 🛠️ Learning Modules

### 🧠 Chapter 1: Conversational Intelligence
**Core dialog systems and reasoning frameworks**
- Foundation models with long-context processing capabilities
- Instruction following with chain-of-thought reasoning
- Tool-augmented agents for mathematical and logical tasks
- In-context learning and multi-turn conversation modeling

**📚 Paper Collection**
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - Vaswani et al., 2017
- [BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805) - Devlin et al., 2018
- [Language Models are Unsupervised Multitask Learners](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) - Radford et al., 2019
- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) - Lewis et al., 2020

### 🧠 Chapter 2: Advanced Reasoning
**Reasoning strategies and cognitive frameworks**
- Chain-of-thought and step-by-step reasoning patterns
- Zero-shot reasoning and emergent problem-solving capabilities
- Self-consistency and consensus-based inference
- Tree-based exploration and deliberate thinking models

**📚 Paper Collection**
- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903) - Wei et al., 2022
- [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916) - Kojima et al., 2022
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171) - Wang et al., 2022
- [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601) - Yao et al., 2023

### 🔍 Chapter 3: Retrieval & Knowledge Engineering  
**Advanced RAG architectures and knowledge graphs**
- Production-grade RAG systems with BGE-m3 and BGE-reranker
- Automated entity extraction and knowledge graph construction
- Chain-of-Thought reasoning for knowledge extraction
- Enterprise NL2SQL with intelligent rejection mechanisms
- Interactive graph visualization with Pyvis and NetworkX

**📚 Paper Collection**
- [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130) - Edge et al., 2024 (Microsoft GraphRAG)
- [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997) - Gao et al., 2023
- [BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation](https://arxiv.org/abs/2402.03216) - Chen et al., 2024
- [RAG vs Fine-tuning: Pipelines, Tradeoffs, and a Case Study on Agriculture](https://arxiv.org/abs/2401.08406) - Ovadia et al., 2024

### 🧠 Chapter 4: Context Engineering
**Advanced context management and optimization strategies**
- KV-Cache optimization and prompt engineering techniques
- Tool masking strategies and dynamic behavior control
- Filesystem-based externalized memory systems
- Attention recitation and goal focus management
- Error preservation and failure learning mechanisms

**📚 Paper Collection**
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - Vaswani et al., 2017
- [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) - Kwon et al., 2023
- [FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691) - Dao, 2023

### 🎨 Chapter 5: Multimodal Models
**Advanced image and document processing**
- Image text recognition and content analysis with Qwen-VL-Max
- Document layout analysis and information extraction
- Multimodal knowledge graph construction
- Cross-modal information fusion and processing

**📚 Paper Collection**
- [Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond](https://arxiv.org/abs/2308.12966) - Bai et al., 2023
- [LayoutParser: A Unified Toolkit for Deep Learning Based Document Image Analysis](https://arxiv.org/abs/2103.15348) - Shen et al., 2021
- [Knowledge Graphs Meet Multi-Modal Learning: A Comprehensive Survey](https://arxiv.org/abs/2402.05391) - Chen et al., 2024

### 🤖 Chapter 6: Expert Multi-Agent Orchestration
**Advanced distributed AI coordination and collaboration patterns**
- Manual function call implementations with Self-Ask pattern
- AutoGen-based function call implementations with ReAct pattern
- Code interpreter capabilities for dynamic problem solving
- Reflexion-based reflection systems with semantic memory
- Advanced inter-agent communication protocols and message passing
- Complex task decomposition and hierarchical planning strategies
- Advanced consensus mechanisms and conflict resolution algorithms
- Distributed reasoning and collaborative problem solving

**📚 Paper Collection**
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171) - Wang et al., 2022 (Self-Ask)
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) - Yao et al., 2022
- [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366) - Shinn et al., 2023
- [Communicative Agents for Software Development](https://arxiv.org/abs/2307.07924) - Qian et al., 2023
- [MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework](https://arxiv.org/abs/2308.00352) - Hong et al., 2023

### 🧪 Chapter 7: Model Fine-Tuning Data Construction
**Comprehensive data pipeline for instruction tuning and preference learning**
- Few-shot format instruction data construction from structured datasets
- Self-Instruct automated data generation and expansion
- Alpaca-style supervised fine-tuning data preparation
- RLHF preference data construction for reward modeling

**📚 Paper Collection**
- [Self-Instruct: Aligning Language Models with Self Generated Instructions](https://arxiv.org/abs/2212.10560) - Wang et al., 2022
- [Stanford Alpaca: An Instruction-following LLaMA Model](https://github.com/tatsu-lab/stanford_alpaca)
- [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) - Ouyang et al., 2022
- [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073) - Bai et al., 2022

### 🧠 Chapter 8: Fine-Tuning Fundamentals
**Historical foundations and modern fine-tuning principles**
- GPT-1 style fine-tuning with frozen embeddings and linear classifiers
- Feature-based transfer learning vs end-to-end fine-tuning
- DashScope embedding integration for sentiment classification
- Educational progression from basic to advanced fine-tuning techniques
- Practical implementation of early fine-tuning methodologies

**📚 Paper Collection**
- [Improving Language Understanding by Generative Pre-Training](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf) - Radford et al., 2018 (GPT-1)
- [Universal Language Model Fine-tuning for Text Classification](https://arxiv.org/abs/1801.06146) - Howard & Ruder, 2018 (ULMFiT)
- [Language Models are Unsupervised Multitask Learners](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) - Radford et al., 2019 (GPT-2)
- [Parameter-Efficient Transfer Learning for NLP](https://arxiv.org/abs/1902.00751) - Houlsby et al., 2019



## ⚡ Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **API Keys**: OpenAI or Alibaba DashScope

### Installation
```bash
git clone https://github.com/tylerelyt/LLM-Workshop.git
cd LLM-Workshop

# Each lesson has its own dependencies - install what you need:
# Chapter 1: Foundation
pip install -r chapter1/lesson1/requirements.txt  # Agent Architectures
pip install -r chapter1/lesson2/requirements.txt  # Mathematical Reasoning
pip install -r chapter1/lesson3/requirements.txt  # Multi-modal Dialogs

# Chapter 2: Advanced Reasoning  
pip install -r chapter2/lesson1/requirements.txt  # Chain-of-Thought
pip install -r chapter2/lesson2/requirements.txt  # Zero-shot Reasoning
pip install -r chapter2/lesson3/requirements.txt  # Tree of Thoughts

# Chapter 3: Advanced Knowledge Engineering
pip install -r chapter3/lesson1/requirements.txt  # RAG System
pip install -r chapter3/lesson2/requirements.txt  # Knowledge Graph
pip install -r chapter3/lesson3/requirements.txt  # NL2SQL

# Chapter 4: Context Engineering
pip install -r chapter4/lesson1/requirements.txt  # KV-Cache Optimization
pip install -r chapter4/lesson2/requirements.txt  # Tool Masking Strategy
pip install -r chapter4/lesson3/requirements.txt  # Filesystem Memory
pip install -r chapter4/lesson4/requirements.txt  # Attention Recitation
pip install -r chapter4/lesson5/requirements.txt  # Error Preservation

# Chapter 5: Multimodal Models
pip install -r chapter5/lesson1/requirements.txt  # Image Content Analysis
pip install -r chapter5/lesson2/requirements.txt  # Document Processing

# Chapter 6: Expert Multi-Agent Orchestration
pip install -r chapter6/lesson1/requirements.txt  # Manual Function Call with Self-Ask
pip install -r chapter6/lesson2/requirements.txt  # AutoGen Function Call Demo
pip install -r chapter6/lesson3/requirements.txt  # Code Interpreter Workshop
pip install -r chapter6/lesson4/requirements.txt  # Reflection System Demo

# Chapter 7: Model Fine-Tuning Data Construction
pip install -r chapter7/lesson1/requirements.txt  # Few-shot Data Construction
pip install -r chapter7/lesson2/requirements.txt  # Self-Instruct Generation
pip install -r chapter7/lesson3/requirements.txt  # Alpaca Data Processing
pip install -r chapter7/lesson4/requirements.txt  # RLHF Preference Data

# Chapter 8: Fine-Tuning Fundamentals
pip install -r chapter8/lesson1/requirements.txt  # GPT-1 Style Fine-tuning
```

### Environment Setup
```bash
# Required: Set your LLM API key (DashScope is default and recommended)
export DASHSCOPE_API_KEY="your-dashscope-key"

# Optional: OpenAI as backup (some exercises support both)
export OPENAI_API_KEY="your-openai-key"

# Recommended: Use virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Start Building
```bash
# Build an interactive knowledge graph from scratch
cd chapter3/lesson2
python knowledge_pipeline.py

# Create production-grade RAG systems
cd chapter3/lesson1
python rag_pipeline.py

# Develop enterprise NL2SQL systems
cd chapter3/lesson3
python nl2sql_engine.py

# Build context engineering systems
cd chapter4/lesson1
python example.py

# Build manual function call systems with Self-Ask pattern
cd chapter6/lesson1
python function_call_workshop.py

# Create AutoGen-based function call systems
cd chapter6/lesson2
python autogen_function_call_demo.py

# Develop code interpreter capabilities
cd chapter6/lesson3
python code_interpreter_workshop.py

# Build reflection systems with semantic memory
cd chapter6/lesson4
python reflection_system_demo.py

# Analyze images and documents
cd chapter5/lesson1
python image_analyzer.py

# Build Few-shot instruction data from structured datasets
cd chapter7/lesson1
python construct_fewshot.py --input-file data/sentiment_demo.json --task-type sentiment --output-path data/fewshot_sentiment.jsonl

# Generate Self-Instruct data expansion (single-file workshop)
cd chapter7/lesson2
python self_instruct_workshop.py

# Convert to Alpaca format for fine-tuning
cd chapter7/lesson3
python alpaca_constructor.py --input-file ../lesson1/data/fewshot_sentiment.jsonl --conversion-type fewshot_to_alpaca --output-path data/alpaca_data.jsonl

# Construct RLHF preference pairs
cd chapter7/lesson4
python rlhf_constructor.py --input-file ../lesson3/data/alpaca_data.jsonl --method model_comparison --high-model qwen-plus --low-model qwen-turbo --output-path data/rlhf_pairs.jsonl

# Learn GPT-1 fine-tuning principles with DashScope embeddings
cd chapter8/lesson1
python dashscope_lr_sentiment.py --input-file data/sentiment_demo.json --batch-size 5
```



## 🆘 Troubleshooting

**Getting Updates**
```bash
git pull origin main  # Get latest code and resources
```

**Common Issues**
- **Environment Setup**: Ensure all dependencies are installed per documentation
- **API Keys**: Verify your LLM API keys are properly configured
- **Python Version**: Requires Python 3.8+ with compatible packages

For persistent issues, check lesson-specific README files or open an issue.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** this repository
2. **Create** a feature branch (`git checkout -b feature-amazing`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature-amazing`)
5. **Open** a Pull Request

## 👥 Contributors

<a href="https://github.com/tylerelyt/LLM-Workshop/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=tylerelyt/LLM-Workshop" />
</a>

## 📈 Stargazers Over Time

[![Stargazers over time](https://starchart.cc/tylerelyt/LLM-Workshop.svg?variant=adaptive)](https://starchart.cc/tylerelyt/LLM-Workshop)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details. You are free to use, modify, and distribute this code for any purpose, including commercial use.

## 🎯 Who Should Join This Workshop

**LLM-Workshop** is designed for developers who learn best by building real projects:

- **🚀 Aspiring AI Engineers** - Build your first production LLM applications
- **💻 Full-Stack Developers** - Add AI capabilities to your existing skills
- **🔬 Research Engineers** - Bridge the gap between papers and production code  
- **🏗️ System Builders** - Learn scalable AI architecture patterns through practice

> Learn by doing: Each module takes you from concept to working implementation, building real systems you can deploy and extend.
