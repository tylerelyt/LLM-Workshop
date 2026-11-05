import os
import json
from typing import List, Dict, Any, Optional

import orjson
import typer
from tqdm import tqdm


app = typer.Typer(add_completion=False, no_args_is_help=True)


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """加载不同格式的数据文件"""
    data = []
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif file_path.endswith('.jsonl'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f if line.strip()]
    return data


def call_model(provider: str, model: str, prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
    """调用指定模型生成回答"""
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    
    elif provider == "dashscope":
        import dashscope
        from http import HTTPStatus
        resp = dashscope.Generation.call(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if resp.status_code == HTTPStatus.OK:
            return resp.output.text.strip()
        else:
            raise RuntimeError(f"DashScope error: {resp.code} {resp.message}")
    
    else:
        raise ValueError(f"不支持的提供商: {provider}")


def generate_preference_pair(
    prompt: str, 
    provider: str,
    high_model: str = "qwen-max",
    low_model: str = "qwen-plus",
    temperature: float = 0.7
) -> Dict[str, str]:
    """
    使用高级模型和低级模型生成偏好对
    高级模型的回答作为 chosen，低级模型的回答作为 rejected
    """
    try:
        # 用高级模型生成高质量回答
        chosen_response = call_model(provider, high_model, prompt, temperature)
        
        # 用低级模型生成较低质量回答
        rejected_response = call_model(provider, low_model, prompt, temperature)
        
        return {
            "prompt": prompt,
            "chosen": chosen_response,
            "rejected": rejected_response,
            "chosen_model": high_model,
            "rejected_model": low_model
        }
    
    except Exception as e:
        return {
            "prompt": prompt,
            "chosen": f"生成失败: {e}",
            "rejected": f"生成失败: {e}",
            "chosen_model": high_model,
            "rejected_model": low_model,
            "error": str(e)
        }


def extract_prompt_from_alpaca(item: Dict[str, Any]) -> str:
    """从 Alpaca 格式提取完整的 prompt"""
    instruction = item.get("instruction", "").strip()
    input_text = item.get("input", "").strip()
    
    if input_text:
        return f"{instruction}\n\n{input_text}"
    else:
        return instruction


def extract_prompt_from_fewshot(item: Dict[str, Any]) -> str:
    """从 Few-shot 格式提取简化的 prompt"""
    fewshot_instruction = item.get("instruction", "")
    
    # 提取任务描述（第一行）
    lines = fewshot_instruction.split('\n')
    task_description = lines[0] if lines else "请回答以下问题"
    
    # 提取目标输入（最后的引号内容）
    import re
    quotes = re.findall(r'"([^"]+)"', fewshot_instruction)
    target_input = quotes[-1] if quotes else ""
    
    if target_input:
        # 简化任务描述
        task_description = task_description.replace("这段话表达了什么情感？请判断是正面还是负面：", "判断以下文本的情感倾向")
        task_description = task_description.replace("分析以下文本的情感倾向：", "判断以下文本的情感倾向")
        return f"{task_description}\n\n文本：{target_input}"
    else:
        return task_description


def save_jsonl(records: List[Dict], output_path: str) -> None:
    """保存JSONL格式数据"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec))
            f.write(b"\n")


def analyze_preference_data(records: List[Dict[str, str]]) -> Dict[str, Any]:
    """分析偏好数据的质量"""
    if not records:
        return {"error": "没有数据可分析"}
    
    chosen_lengths = [len(r.get("chosen", "")) for r in records if "error" not in r]
    rejected_lengths = [len(r.get("rejected", "")) for r in records if "error" not in r]
    
    valid_pairs = [r for r in records if "error" not in r]
    error_count = len(records) - len(valid_pairs)
    
    analysis = {
        "total_pairs": len(records),
        "valid_pairs": len(valid_pairs),
        "error_pairs": error_count,
        "success_rate": len(valid_pairs) / len(records) if records else 0,
    }
    
    if chosen_lengths and rejected_lengths:
        analysis.update({
            "avg_chosen_length": sum(chosen_lengths) / len(chosen_lengths),
            "avg_rejected_length": sum(rejected_lengths) / len(rejected_lengths),
            "length_ratio": sum(chosen_lengths) / sum(rejected_lengths) if sum(rejected_lengths) > 0 else 0,
        })
    
    return analysis


@app.command()
def main(
    input_file: str = typer.Option(..., help="输入数据文件路径"),
    method: str = typer.Option("model_comparison", help="构造方法: model_comparison, generate_pairs, rank_responses"),
    output_path: str = typer.Option("data/rlhf_preference.jsonl", help="输出 RLHF 偏好数据路径"),
    provider: str = typer.Option("dashscope", help="模型提供商: openai 或 dashscope"),
    high_model: str = typer.Option("qwen-max", help="高级模型名称 (生成 chosen 回答)"),
    low_model: str = typer.Option("qwen-plus", help="低级模型名称 (生成 rejected 回答)"),
    max_samples: int = typer.Option(-1, help="最大处理样本数，-1表示处理所有"),
    temperature: float = typer.Option(0.7, help="采样温度"),
    enable_analysis: bool = typer.Option(True, help="是否生成数据质量分析报告"),
):
    """构造 RLHF (Reinforcement Learning from Human Feedback) 偏好训练数据"""
    
    # 加载数据
    typer.echo(f"加载数据文件: {input_file}")
    raw_data = load_data(input_file)
    
    if max_samples > 0:
        raw_data = raw_data[:max_samples]
    
    typer.echo(f"处理 {len(raw_data)} 条数据")
    typer.echo(f"高级模型 (chosen): {high_model}")
    typer.echo(f"低级模型 (rejected): {low_model}")
    
    # 构造偏好对数据
    preference_pairs = []
    
    for item in tqdm(raw_data, desc="构造偏好对数据"):
        try:
            if method == "model_comparison":
                # 从输入数据提取 prompt
                if "instruction" in item and "input" in item:
                    # Alpaca 格式
                    prompt = extract_prompt_from_alpaca(item)
                elif "instruction" in item:
                    # Few-shot 格式
                    prompt = extract_prompt_from_fewshot(item)
                else:
                    # 直接的 prompt 格式
                    prompt = item.get("prompt", item.get("text", ""))
                
                if not prompt:
                    typer.echo(f"跳过无效数据: {item}")
                    continue
                
                # 使用高低级模型生成偏好对
                pair = generate_preference_pair(
                    prompt=prompt,
                    provider=provider,
                    high_model=high_model,
                    low_model=low_model,
                    temperature=temperature
                )
                preference_pairs.append(pair)
            
            elif method == "generate_pairs":
                # 其他方法的实现可以在这里添加
                typer.echo("generate_pairs 方法尚未实现")
                break
                
            elif method == "rank_responses":
                # 其他方法的实现可以在这里添加
                typer.echo("rank_responses 方法尚未实现")
                break
                
        except Exception as e:
            typer.echo(f"处理数据时出错: {e}")
            continue
    
    # 保存结果
    save_jsonl(preference_pairs, output_path)
    typer.echo(f"成功构造 {len(preference_pairs)} 条偏好对数据")
    
    # 数据质量分析
    if enable_analysis and preference_pairs:
        analysis = analyze_preference_data(preference_pairs)
        typer.echo("\n=== 数据质量分析 ===")
        typer.echo(f"总偏好对数: {analysis['total_pairs']}")
        typer.echo(f"有效偏好对: {analysis['valid_pairs']}")
        typer.echo(f"成功率: {analysis['success_rate']:.2%}")
        
        if 'avg_chosen_length' in analysis:
            typer.echo(f"chosen 平均长度: {analysis['avg_chosen_length']:.1f}")
            typer.echo(f"rejected 平均长度: {analysis['avg_rejected_length']:.1f}")
            typer.echo(f"长度比率 (chosen/rejected): {analysis['length_ratio']:.2f}")
    
    typer.echo(f"偏好数据保存至: {output_path}")


if __name__ == "__main__":
    app()
