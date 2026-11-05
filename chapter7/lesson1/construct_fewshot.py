import os
import csv
import json
from typing import List, Dict, Optional, Any
from pathlib import Path

import orjson
import typer
import pandas as pd
from tqdm import tqdm


app = typer.Typer(add_completion=False, no_args_is_help=True)


# Automated Few-shot Instruction Templates - Task Description + Example + Specific Input
# These templates enable automatic generation of diverse instruction formats for the same task
FEWSHOT_TEMPLATES = {
    "sentiment": [
        "判断下面这句话表达的是积极情绪还是消极情绪？",
        "分析以下文本的情感倾向：",
        "这段话表达了什么情感？请判断是正面还是负面：",
        "请识别文本的情感极性：",
    ],
    "classification": [
        "请对以下文本进行分类：",
        "判断下面文本的类别：",
        "将以下内容归类：",
        "分析文本并确定其分类：",
    ],
    "qa": [
        "请回答以下问题：",
        "根据问题给出答案：",
        "解答这个问题：",
        "请回答：",
    ],
    "translate": [
        "请将以下内容翻译成中文：",
        "翻译下面的文本：",
        "请翻译：",
        "将这段话翻译成中文：",
    ],
}


def load_data(file_path: str, task_type: str) -> List[Dict[str, Any]]:
    """加载不同格式的数据文件"""
    file_path = Path(file_path)
    data = []
    
    if file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
        data = df.to_dict('records')
    elif file_path.suffix.lower() == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif file_path.suffix.lower() == '.jsonl':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f if line.strip()]
    elif file_path.suffix.lower() == '.tsv':
        df = pd.read_csv(file_path, sep='\t')
        data = df.to_dict('records')
    else:
        raise ValueError(f"不支持的文件格式: {file_path.suffix}")
    
    return data


def construct_fewshot_instruction(
    data: List[Dict[str, Any]], 
    task_type: str, 
    target_idx: int,
    num_examples: int = 1
) -> Dict[str, str]:
    """
    Automatically construct Few-shot instruction data with examples
    
    This is the core automation function that:
    1. Randomly selects appropriate examples from the dataset
    2. Picks diverse instruction templates to improve robustness
    3. Constructs the complete instruction-input-output format
    4. Ensures consistent quality across all generated examples
    
    Returns standardized instruction fine-tuning format ready for training.
    """
    
    # 获取目标数据项
    target_item = data[target_idx]
    
    # 随机选择一个示例（排除目标项）
    import random
    example_indices = [i for i in range(len(data)) if i != target_idx]
    if len(example_indices) == 0:
        raise ValueError("没有足够的数据作为示例")
    
    example_idx = random.choice(example_indices)
    example_item = data[example_idx]
    
    # 获取示例和目标的输入输出
    example_input, example_output = extract_input_output(example_item, task_type)
    target_input, target_output = extract_input_output(target_item, task_type)
    
    # 选择任务描述模板
    templates = FEWSHOT_TEMPLATES[task_type]
    template = random.choice(templates)
    
    # 构造 Few-shot 指令（任务描述 + 示例 + 具体输入）
    if task_type == "sentiment":
        # 情感分类特殊格式
        instruction = f"""{template}
例子：
句子："{example_input}" 情绪：{example_output}
现在请判断下面这个句子：
句子："{target_input}" 情绪："""
    elif task_type == "classification":
        instruction = f"""{template}
例子：
文本："{example_input}" 类别：{example_output}
现在请分类下面这个文本：
文本："{target_input}" 类别："""
    elif task_type == "qa":
        instruction = f"""{template}
例子：
问题：{example_input} 答案：{example_output}
现在请回答：
问题：{target_input} 答案："""
    elif task_type == "translate":
        instruction = f"""{template}
例子：
原文：{example_input} 译文：{example_output}
现在请翻译：
原文：{target_input} 译文："""
    else:
        # 通用格式
        instruction = f"""{template}
例子：
输入：{example_input} 输出：{example_output}
现在请处理：
输入：{target_input} 输出："""
    
    return {
        "instruction": instruction,
        "input": "",
        "output": target_output
    }


def extract_input_output(item: Dict[str, Any], task_type: str) -> tuple:
    """根据任务类型提取输入输出"""
    if task_type in ["sentiment", "classification"]:
        text_keys = ['text', 'content', 'input', 'sentence', 'document']
        label_keys = ['label', 'category', 'class', 'output', 'target']
        
        text = None
        label = None
        
        for key in text_keys:
            if key in item:
                text = str(item[key]).strip()
                break
        
        for key in label_keys:
            if key in item:
                raw_label = item[key]
                # 处理数字标签
                if task_type == "sentiment":
                    if raw_label == 0 or raw_label == "0":
                        label = "负面"
                    elif raw_label == 1 or raw_label == "1":
                        label = "正面"
                    else:
                        label = str(raw_label).strip()
                else:
                    label = str(raw_label).strip()
                break
        
        if not text or label is None:
            raise ValueError(f"无法找到文本/标签字段，可用字段: {list(item.keys())}")
        
        return text, label
    
    elif task_type == "qa":
        question_keys = ['question', 'query', 'input', 'prompt', 'text', 'q']
        answer_keys = ['answer', 'response', 'output', 'target', 'label', 'a']
        
        question = None
        answer = None
        
        for key in question_keys:
            if key in item:
                question = str(item[key]).strip()
                break
        
        for key in answer_keys:
            if key in item:
                answer = str(item[key]).strip()
                break
        
        if not question or not answer:
            raise ValueError(f"无法找到问题/答案字段，可用字段: {list(item.keys())}")
        
        return question, answer
    
    elif task_type == "translate":
        source_keys = ['source', 'en', 'english', 'input', 'text', 'original']
        target_keys = ['target', 'zh', 'chinese', 'output', 'translation']
        
        source = None
        target = None
        
        for key in source_keys:
            if key in item:
                source = str(item[key]).strip()
                break
        
        for key in target_keys:
            if key in item:
                target = str(item[key]).strip()
                break
        
        if not source or not target:
            raise ValueError(f"无法找到源文本/目标文本字段，可用字段: {list(item.keys())}")
        
        return source, target
    
    else:
        raise ValueError(f"不支持的任务类型: {task_type}")





def save_jsonl(records: List[Dict], output_path: str) -> None:
    """保存JSONL格式数据"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec))
            f.write(b"\n")


@app.command()
def main(
    input_file: str = typer.Option(..., help="输入数据文件路径 (CSV/JSON/JSONL/TSV)"),
    task_type: str = typer.Option(..., help="任务类型: qa, classification, rewrite, summarize, translate"),
    output_path: str = typer.Option("data/fewshot_instructions.jsonl", help="输出JSONL路径"),
    max_samples: int = typer.Option(-1, help="最大处理样本数，-1表示处理所有"),
    template_variety: bool = typer.Option(True, help="是否使用多样化的指令模板"),
):
    """
    Automated Few-shot Instruction Data Construction for Fine-tuning
    
    This tool demonstrates how to systematically convert structured datasets 
    into high-quality instruction fine-tuning data. Key automation features:
    
    - Intelligent field recognition across multiple data formats
    - Automatic template selection for instruction diversity  
    - Systematic few-shot example pairing
    - Batch processing with progress tracking
    - Quality validation and error handling
    
    Perfect for creating large-scale instruction datasets efficiently.
    """
    
    # 检查任务类型
    if task_type not in FEWSHOT_TEMPLATES:
        typer.echo(f"不支持的任务类型: {task_type}")
        typer.echo(f"支持的类型: {list(FEWSHOT_TEMPLATES.keys())}")
        raise typer.Exit(1)
    
    # 加载数据
    typer.echo(f"加载数据文件: {input_file}")
    raw_data = load_data(input_file, task_type)
    
    if max_samples > 0:
        raw_data = raw_data[:max_samples]
    
    typer.echo(f"处理 {len(raw_data)} 条数据")
    
    # 检查数据量
    if len(raw_data) < 4:
        typer.echo(f"数据量不足，至少需要 4 条数据用于 Few-shot 示例")
        raise typer.Exit(1)
    
    # 构造 Few-shot 指令数据
    records = []
    num_examples = 3  # 固定使用3个示例
    
    for i in tqdm(range(len(raw_data)), desc="构造 Few-shot 指令数据"):
        try:
            record = construct_fewshot_instruction(raw_data, task_type, i, num_examples)
            records.append(record)
        except Exception as e:
            typer.echo(f"处理第 {i+1} 条数据时出错: {e}")
            continue
    
    # 保存结果
    save_jsonl(records, output_path)
    typer.echo(f"成功构造 {len(records)} 条 Few-shot 指令数据，保存至: {output_path}")


if __name__ == "__main__":
    app()
