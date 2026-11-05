# Chapter 7: Model Fine-Tuning Data Construction

This chapter focuses on constructing high-quality training data for various large language model fine-tuning methods. It covers everything from basic Few-shot format to advanced preference learning data construction techniques.

## 📚 Chapter Structure

### Lesson 1: Few-shot Format Instruction Fine-tuning Data Construction
- **Objective**: Convert structured data to natural language instruction format
- **Core**: "Task Description + Example + Specific Input" Few-shot pattern
- **Supported Tasks**: Sentiment analysis, text classification, Q&A, translation, etc.
- **File**: `construct_fewshot.py`

### Lesson 2: Self-Instruct Data Construction  
- **Objective**: Automatically generate instruction-output pairs
- **Core**: Use LLMs to automatically generate diverse instruction data
- **Supported APIs**: OpenAI, DashScope (auto-switch)
- **File**: `self_instruct_workshop.py` (single-file workflow)

### Lesson 3: Alpaca Data Processing
- **Objective**: Convert to Stanford Alpaca standard format and validate data quality
- **Core**: Standardized `instruction`, `input`, `output` structure; cleaning and validation
- **Features**: Data quality filtering, schema checks, and basic statistics
- **File**: `alpaca_constructor.py`
- **Note**: Focuses on data processing only; does not include LoRA code or training scripts

### Lesson 4: RLHF Training Data Construction
- **Objective**: Construct human feedback preference learning data
- **Core**: Model comparison method for generating preference pairs
- **Format**: `prompt`, `chosen`, `rejected` triplets
- **File**: `rlhf_constructor.py`



## 🚀 Quick Start

### Environment Setup
```bash
# Set API keys (DashScope is default and recommended)
export DASHSCOPE_API_KEY="your-dashscope-key"
# Optional: OpenAI as backup
export OPENAI_API_KEY="your-openai-key"

# Install dependencies
pip install -r lesson1/requirements.txt
pip install -r lesson2/requirements.txt
pip install -r lesson3/requirements.txt
pip install -r lesson4/requirements.txt

```

### Data Construction Pipeline

1. **Few-shot Data Construction**
```bash
cd lesson1
python construct_fewshot.py --input-file data/sentiment_demo.json --task-type sentiment --output-path data/fewshot_output.jsonl
```

2. **Self-Instruct Data Generation**
```bash
cd lesson2
python self_instruct_workshop.py
```

3. **Alpaca Data Processing**
```bash
cd lesson3
python alpaca_constructor.py --input-file ../lesson1/data/fewshot_output.jsonl --output-path data/alpaca_output.jsonl
```

4. **RLHF Preference Pair Construction**
```bash
cd lesson4
python rlhf_constructor.py --input-file ../lesson3/data/alpaca_output.jsonl --method model_comparison --high-model qwen-plus --low-model qwen-turbo --output-path data/rlhf_output.jsonl
```



## 📖 Related Papers

- **Self-Instruct**: [Self-Instruct: Aligning Language Model with Self Generated Instructions](https://arxiv.org/abs/2212.10560)
- **Stanford Alpaca**: [Stanford Alpaca: An Instruction-following LLaMA model](https://github.com/tatsu-lab/stanford_alpaca)
- **LoRA**: [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- **QLoRA**: [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)
- **RLHF**: [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155)
- **Constitutional AI**: [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)

## 🎯 Learning Objectives

Through this chapter, you will master:

1. **Data Format Conversion**: Convert raw data to various fine-tuning formats
2. **Template Design**: Design effective instruction templates and prompts
3. **Quality Control**: Implement data filtering and quality assessment
4. **Preference Learning**: Construct RLHF preference data
5. **Automated Workflows**: Build end-to-end data construction pipelines

## 💡 Best Practices

1. **Data Diversity**: Use multiple templates and examples to increase data diversity
2. **Quality Assessment**: Regularly evaluate the quality and effectiveness of generated data
3. **Cost Control**: Wisely choose models to balance quality and cost
4. **Version Management**: Save data construction configurations and results for reproducibility
5. **Incremental Construction**: Support incremental data construction and updates

---

**Note**: Please ensure you have properly set up the corresponding API keys before using API services, and understand the associated usage costs.
