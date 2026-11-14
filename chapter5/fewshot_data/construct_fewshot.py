import os
import csv
import json
import random
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
    num_examples: int = 1,
    template_variety: bool = True,
) -> Dict[str, str]:
    """为目标行配对示例并保留原始答案；内容质量需要另行复核。"""

    # 获取目标数据项
    target_item = data[target_idx]
    
    example_indices = [i for i in range(len(data)) if i != target_idx]
    if not 1 <= num_examples <= len(example_indices):
        raise ValueError("示例数量须至少为 1，并小于原始记录总数。")
    example_items = [data[i] for i in random.sample(example_indices, num_examples)]
    examples = [extract_input_output(item, task_type) for item in example_items]
    target_input, target_output = extract_input_output(target_item, task_type)

    # 选择任务描述模板
    templates = FEWSHOT_TEMPLATES[task_type]
    # 两条路径消耗相同的随机抽样，固定种子后示例配对保持一致。
    sampled_template = random.choice(templates)
    template = sampled_template if template_variety else templates[0]
    
    # 构造 Few-shot 指令（任务描述 + 示例 + 具体输入）
    if task_type == "sentiment":
        example_text = "\n".join(f'句子："{text}" 情绪：{answer}' for text, answer in examples)
        instruction = f"""{template}
例子：
{example_text}
现在请判断下面这个句子：
句子："{target_input}" 情绪："""
    elif task_type == "classification":
        example_text = "\n".join(f'文本："{text}" 类别：{answer}' for text, answer in examples)
        instruction = f"""{template}
例子：
{example_text}
现在请分类下面这个文本：
文本："{target_input}" 类别："""
    elif task_type == "qa":
        example_text = "\n".join(f"问题：{text} 答案：{answer}" for text, answer in examples)
        instruction = f"""{template}
例子：
{example_text}
现在请回答：
问题：{target_input} 答案："""
    elif task_type == "translate":
        example_text = "\n".join(f"原文：{text} 译文：{answer}" for text, answer in examples)
        instruction = f"""{template}
例子：
{example_text}
现在请翻译：
原文：{target_input} 译文："""
    else:
        raise ValueError(f"不支持的任务类型: {task_type}")
    
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
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec))
            f.write(b"\n")


@app.command()
def main(
    input_file: str = typer.Option(..., help="输入数据文件路径 (CSV/JSON/JSONL/TSV)"),
    task_type: str = typer.Option(..., help="任务类型: sentiment, classification, qa, translate"),
    output_path: str = typer.Option("data/fewshot_instructions.jsonl", help="输出JSONL路径"),
    max_samples: int = typer.Option(-1, help="最大处理样本数，-1表示处理所有"),
    template_variety: bool = typer.Option(True, help="是否使用多样化的指令模板"),
    num_examples: int = typer.Option(1, min=1, help="每条指令的配对示例数量"),
    seed: Optional[int] = typer.Option(None, help="固定配对和模板抽样的随机种子"),
):
    """将标注数据组合为含示例的指令记录，供逐条复核。"""
    if seed is not None:
        random.seed(seed)

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
    if len(raw_data) <= num_examples:
        typer.echo(f"数据量不足，{num_examples} 个配对示例至少需要 {num_examples + 1} 条原始记录")
        raise typer.Exit(1)
    
    # 构造 Few-shot 指令数据
    records = []
    preview_source = None
    
    for i in tqdm(range(len(raw_data)), desc="构造 Few-shot 指令数据"):
        try:
            record = construct_fewshot_instruction(raw_data, task_type, i, num_examples, template_variety)
            records.append(record)
            if preview_source is None:
                preview_source = raw_data[i]
        except Exception as e:
            typer.echo(f"处理第 {i+1} 条数据时出错: {e}")
            continue
    
    if not records:
        typer.echo("没有可保存的记录，请检查输入字段和标签。", err=True)
        raise typer.Exit(1)
    typer.echo("\n=== 实际样本：原始记录 → 配对指令 ===")
    typer.echo(json.dumps(preview_source, ensure_ascii=False))
    typer.echo(records[0]["instruction"])
    typer.echo(f"目标答案（沿用原标签）：{records[0]['output']}")
    typer.echo("核对：示例与目标是否不同，示例标签和目标答案是否各自正确。")
    # 保存结果
    save_jsonl(records, output_path)
    typer.echo(f"成功构造 {len(records)} 条 Few-shot 指令数据，保存至: {output_path}")


if __name__ == "__main__":
    app()
