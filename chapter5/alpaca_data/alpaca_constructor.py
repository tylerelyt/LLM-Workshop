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
    # 对应第 1 课的四种模板，保留无引号、多行及包含引号的目标文本。
    pattern = (
        r'(?:^|\n)现在请[^\n]*[：:]\s*\n(?:句子|文本|问题|原文)[：:]'
        r'(.*?)(?:情绪|类别|答案|译文)[：:]\s*$'
    )
    match = re.search(pattern, fewshot_instruction, re.DOTALL)
    if match:
        target = match.group(1).strip()
        if len(target) >= 2 and target[0] == target[-1] == '"':
            target = target[1:-1]
        return target

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
    target_input = item.get('input') or extract_target_input(fewshot_instruction)
    
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
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec))
            f.write(b"\n")


def filter_with_decisions(records):
    """返回通过记录及逐条决策，展示与实际过滤使用同一规则。"""
    filtered, decisions, seen = [], [], set()
    for number, record in enumerate(records, 1):
        instruction = record.get("instruction", "").strip()
        input_text = record.get("input", "").strip()
        output = record.get("output", "").strip()
        key = (instruction, input_text)
        if len(instruction) < 5:
            reason = "指令少于 5 字"
        elif not output:
            reason = "答案为空"
        elif len(instruction) > 500 or len(output) > 2000:
            reason = "指令超过 500 字或答案超过 2000 字"
        elif key in seen:
            reason = "指令与输入重复"
        else:
            reason = ""
            seen.add(key)
            filtered.append(record)
        decisions.append({"number": number, "record": record, "reason": reason})
    return filtered, decisions


def filter_quality(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """兼容直接调用；内容正确性仍需人工复核。"""
    return filter_with_decisions(records)[0]


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
    sources = []
    
    for source_number, item in enumerate(tqdm(raw_data, desc="转换为 Alpaca 格式"), 1):
        try:
            alpaca_record = converter(item)
            records.append(alpaca_record)
            sources.append((source_number, item))
        except Exception as e:
            typer.echo(f"转换失败: {e}")
            continue
    
    # 质量过滤
    if enable_filtering:
        typer.echo(f"转换完成，开始基础规则过滤...")
        original_count = len(records)
        records, decisions = filter_with_decisions(records)
        typer.echo(f"过滤完成: {original_count} -> {len(records)} 条数据")
    
    else:
        decisions = [{"number": i, "record": row, "reason": ""} for i, row in enumerate(records, 1)]
    typer.echo("\n=== 实际转换与过滤（每类最多展示一条） ===")
    for rejected in (False, True):
        decision = next((d for d in decisions if bool(d["reason"]) == rejected), None)
        if decision is None:
            typer.echo("本轮没有被过滤的样本。" if rejected else "本轮没有保留样本。")
            continue
        source_number, source = sources[decision["number"] - 1]
        typer.echo(f"原始记录 #{source_number}：{json.dumps(source, ensure_ascii=False)}")
        for field, value in decision["record"].items():
            typer.echo(f"  {field}: {value}")
        retained = "保留；通过基础规则，内容仍需复核" if enable_filtering else "保留；未启用过滤，尚未校验"
        typer.echo(f"  决策：过滤；{decision['reason']}" if rejected else f"  决策：{retained}")
    if not records:
        typer.echo("没有可保存的 Alpaca 样本，请检查输入格式和质量过滤。", err=True)
        raise typer.Exit(1)
    save_jsonl(records, output_path)
    typer.echo(f"成功构造 {len(records)} 条 Alpaca 格式数据，保存至: {output_path}")


if __name__ == "__main__":
    app()
