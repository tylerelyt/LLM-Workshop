import os
import json
import re
from typing import List, Dict, Any
from pathlib import Path

import orjson
import typer
import pandas as pd
from tqdm import tqdm


app = typer.Typer(add_completion=False, no_args_is_help=True)


def load_data(file_path: str) -> List[Dict[str, Any]]:
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
    else:
        raise ValueError(f"不支持的文件格式: {file_path.suffix}")
    
    return data


def extract_clean_instruction(fewshot_instruction: str) -> str:
    """从 Few-shot 指令中提取干净的任务描述"""
    # 匹配任务描述部分（第一行到"例子："之前）
    lines = fewshot_instruction.strip().split('\n')
    task_description = lines[0]
    
    # 清理常见的提示词
    task_description = re.sub(r'[：:]$', '', task_description)
    task_description = task_description.replace('请判断是正面还是负面', '判断情感倾向')
    task_description = task_description.replace('现在请判断下面这个句子', '判断以下句子的情感')
    
    return task_description.strip()


def extract_target_input(fewshot_instruction: str) -> str:
    """从 Few-shot 指令中提取目标输入"""
    # 匹配"现在请..."部分的输入
    pattern = r'现在请[^：:]*[：:][^"]*"([^"]+)"'
    match = re.search(pattern, fewshot_instruction)
    if match:
        return match.group(1)
    
    # 备用模式：匹配最后出现的引号内容
    quotes = re.findall(r'"([^"]+)"', fewshot_instruction)
    if quotes:
        return quotes[-1]
    
    return ""


def fewshot_to_alpaca(item: Dict[str, Any]) -> Dict[str, str]:
    """将 Few-shot 格式转换为 Alpaca 格式"""
    fewshot_instruction = item.get('instruction', '')
    output = item.get('output', '')
    
    # 提取简洁的指令和输入
    clean_instruction = extract_clean_instruction(fewshot_instruction)
    target_input = extract_target_input(fewshot_instruction)
    
    return {
        "instruction": clean_instruction,
        "input": target_input,
        "output": output
    }


def qa_to_alpaca(item: Dict[str, Any]) -> Dict[str, str]:
    """将问答格式转换为 Alpaca 格式"""
    question_keys = ['question', 'query', 'input', 'prompt', 'q']
    answer_keys = ['answer', 'response', 'output', 'a']
    
    question = ""
    answer = ""
    
    for key in question_keys:
        if key in item:
            question = str(item[key]).strip()
            break
    
    for key in answer_keys:
        if key in item:
            answer = str(item[key]).strip()
            break
    
    return {
        "instruction": "请回答以下问题",
        "input": question,
        "output": answer
    }


def chat_to_alpaca(item: Dict[str, Any]) -> Dict[str, str]:
    """将对话格式转换为 Alpaca 格式"""
    if 'conversations' in item:
        conversations = item['conversations']
        if len(conversations) >= 2:
            user_msg = conversations[0].get('value', '')
            assistant_msg = conversations[1].get('value', '')
            return {
                "instruction": "请回应以下对话",
                "input": user_msg,
                "output": assistant_msg
            }
    
    # 简单的 user/assistant 格式
    user_text = item.get('user', item.get('human', ''))
    assistant_text = item.get('assistant', item.get('gpt', ''))
    
    return {
        "instruction": "请回应以下对话",
        "input": user_text,
        "output": assistant_text
    }


def classification_to_alpaca(item: Dict[str, Any]) -> Dict[str, str]:
    """将分类数据转换为 Alpaca 格式"""
    text_keys = ['text', 'content', 'sentence', 'document']
    label_keys = ['label', 'category', 'class']
    
    text = ""
    label = ""
    
    for key in text_keys:
        if key in item:
            text = str(item[key]).strip()
            break
    
    for key in label_keys:
        if key in item:
            label = str(item[key]).strip()
            break
    
    return {
        "instruction": "对以下文本进行分类",
        "input": text,
        "output": label
    }


def save_jsonl(records: List[Dict], output_path: str) -> None:
    """保存JSONL格式数据"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec))
            f.write(b"\n")


def filter_quality(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """基本质量过滤"""
    filtered = []
    seen_instructions = set()
    
    for record in records:
        instruction = record.get('instruction', '').strip()
        input_text = record.get('input', '').strip()
        output = record.get('output', '').strip()
        
        # 过滤条件
        if len(instruction) < 5 or len(output) < 3:
            continue
        if len(instruction) > 500 or len(output) > 2000:
            continue
        if instruction in seen_instructions:
            continue
            
        seen_instructions.add(instruction)
        filtered.append(record)
    
    return filtered


@app.command()
def main(
    input_file: str = typer.Option(..., help="输入数据文件路径"),
    conversion_type: str = typer.Option(..., help="转换类型: fewshot_to_alpaca, qa_to_alpaca, chat_to_alpaca, classification_to_alpaca"),
    output_path: str = typer.Option("data/alpaca_data.jsonl", help="输出 Alpaca JSONL 路径"),
    max_samples: int = typer.Option(-1, help="最大处理样本数，-1表示处理所有"),
    enable_filtering: bool = typer.Option(True, help="是否启用质量过滤"),
):
    """将各种格式的数据转换为 Alpaca 训练格式"""
    
    # 转换器映射
    converters = {
        "fewshot_to_alpaca": fewshot_to_alpaca,
        "qa_to_alpaca": qa_to_alpaca,
        "chat_to_alpaca": chat_to_alpaca,
        "classification_to_alpaca": classification_to_alpaca,
    }
    
    if conversion_type not in converters:
        typer.echo(f"不支持的转换类型: {conversion_type}")
        typer.echo(f"支持的类型: {list(converters.keys())}")
        raise typer.Exit(1)
    
    # 加载数据
    typer.echo(f"加载数据文件: {input_file}")
    raw_data = load_data(input_file)
    
    if max_samples > 0:
        raw_data = raw_data[:max_samples]
    
    typer.echo(f"处理 {len(raw_data)} 条数据")
    
    # 转换数据
    converter = converters[conversion_type]
    records = []
    
    for item in tqdm(raw_data, desc="转换为 Alpaca 格式"):
        try:
            alpaca_record = converter(item)
            records.append(alpaca_record)
        except Exception as e:
            typer.echo(f"转换失败: {e}")
            continue
    
    # 质量过滤
    if enable_filtering:
        typer.echo(f"转换完成，开始质量过滤...")
        original_count = len(records)
        records = filter_quality(records)
        typer.echo(f"过滤完成: {original_count} -> {len(records)} 条数据")
    
    # 保存结果
    save_jsonl(records, output_path)
    typer.echo(f"成功构造 {len(records)} 条 Alpaca 格式数据，保存至: {output_path}")


if __name__ == "__main__":
    app()
