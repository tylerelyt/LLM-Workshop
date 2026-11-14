#!/usr/bin/env python3
"""
Chapter 6 Lesson 1: Function Call Workshop
手动实现 Function Call 的核心机制

核心学习目标：
1. 理解 Self-Ask 格式
2. 掌握函数注册和调用机制
3. 观察 LLM 的任务分解能力
"""

import os
import argparse
import copy
from pathlib import Path
import json
import random
from datetime import datetime
import sys
from time import perf_counter
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import load_environment
from chapter8.manual_tool_loop.verification import verify_trace
from openai import OpenAI

# ==================== LLM 调用 ====================
def call_llm(messages, model=None):
    """调用 LLM"""
    try:
        compatible = bool(os.getenv("OPENAI_API_KEY"))
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY") if compatible else os.getenv("DASHSCOPE_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") if compatible else "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini") if compatible else "qwen-max"
        response = client.chat.completions.create(
            model=model or default_model,
            messages=messages,
            temperature=0.3
        )
        answer = response.choices[0].message.content
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("模型没有返回可用正文。")
        return answer
    except Exception as e:
        raise RuntimeError(f"模型接口请求失败，请先修复连接或配置：{e}") from e

# ==================== 工具函数 ====================
def generate_numbers(count=10, min_val=1, max_val=100, seed=None):
    """生成可复现的数据；不改动进程的全局随机数状态。"""
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ValueError("count 必须是正整数。")
    if min_val > max_val:
        raise ValueError("min_val 不能大于 max_val。")
    rng = random.Random(seed)
    numbers = [rng.randint(min_val, max_val) for _ in range(count)]
    return {"description": f"生成 {count} 个随机数", "count": count, "numbers": numbers}


def calculate_stats(numbers, operation="all"):
    """实际计算统计值，拒绝空数据与未知操作。"""
    if isinstance(numbers, str):
        numbers = json.loads(numbers)
    if operation not in {"sum", "avg", "max", "min", "all"}:
        raise ValueError("未知统计操作。")
    numbers = [float(x) for x in numbers]
    if not numbers:
        raise ValueError("numbers 不能为空。")
    result = {"count": len(numbers)}
    if operation in {"sum", "all"}: result["sum"] = sum(numbers)
    if operation in {"avg", "all"}: result["average"] = sum(numbers) / len(numbers)
    if operation in {"max", "all"}: result["maximum"] = max(numbers)
    if operation in {"min", "all"}: result["minimum"] = min(numbers)
    if operation == "all":
        values = sorted(numbers); n = len(values)
        result["median"] = (values[n//2-1]+values[n//2])/2 if n%2==0 else values[n//2]
    return result


def grade_task(count=18, seed=42):
    return (f"生成 {count} 个0—100分的测试分数，随机种子为 {seed}。"
            f"调用 generate_numbers，count={count}、min_val=0、max_val=100、seed={seed}；把真实数列传给 calculate_stats，operation=all，取得完整统计。"
            "平均分在60—80且最低分至少30时才合格。依据实际结果回答合格还是不合格。")

# ==================== 函数注册 ====================
FUNCTIONS = {
    "generate_numbers": {
        "func": generate_numbers,
        "desc": "生成指定数量和范围的随机数列表",
        "params": {"count": "数量", "min_val": "最小值", "max_val": "最大值", "seed": "随机种子（可选）"}
    },
    "calculate_stats": {
        "func": calculate_stats,
        "desc": "计算数字列表的统计信息",
        "params": {"numbers": "数字列表", "operation": "操作类型(sum/avg/max/min/all)"}
    }
}

def get_function_descriptions():
    """获取函数描述"""
    desc = ""
    for name, info in FUNCTIONS.items():
        desc += f"函数: {name}\n功能: {info['desc']}\n参数: {info['params']}\n\n"
    return desc

def execute_function(name, **params):
    if name not in FUNCTIONS:
        return {"error": f"未知函数: {name}"}
    try:
        return FUNCTIONS[name]["func"](**params)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        return {"error": str(error)}

# ==================== Self-Ask 引擎 ====================
class SelfAskEngine:
    def __init__(self, max_steps=5):
        if max_steps < 1:
            raise ValueError("max_steps 必须为正数。")
        self.max_steps = max_steps
        self.history = []
        self.results = {}
        self.trace = []
    
    def get_system_prompt(self):
        """系统提示词"""
        return f"""每轮只做一件事。需要取数据时，输出 Follow up: 加一个函数调用 JSON。
已经拿到足够数据时，输出 So the final answer is: 加结论和依据。

可用函数：
{get_function_descriptions()}

示例：
Follow up: {{"action":"call_function","function":"generate_numbers","parameters":{{"count":3,"seed":42}}}}
收到 Intermediate answer 后，使用其中的真实 numbers 调用 calculate_stats。
收到统计结果后，直接给出结论。只有现有结果缺少所需信息时才再次调用。
不要编造 Intermediate answer，也不要把调用和结论放在同一轮。"""

    def parse_function_call(self, response):
        if "Follow up:" not in response:
            return None
        tail = response.split("Follow up:", 1)[1]
        start = tail.find("{")
        if start < 0:
            return None
        try:
            call, _ = json.JSONDecoder().raw_decode(tail[start:])
        except json.JSONDecodeError:
            return None
        if (not isinstance(call, dict) or not isinstance(call.get("function"), str)
                or not isinstance(call.get("parameters"), dict)):
            return None
        return call

    def process_parameters(self, params):
        # 只解析明确的前序结果引用，不覆盖模型给出的 JSON 数组字符串。
        for key, value in params.items():
            if not isinstance(value, str):
                continue
            for name, result in self.results.items():
                if value in {name, name + "." + key, "$" + name + "." + key} and key in result:
                    params[key] = result[key]
                    break

    def run(self, request):
        """执行完整流程"""
        print(f"🎯 任务: {request}")
        print("="*50)
        
        self.history.append({"role": "user", "content": request})
        
        for step in range(1, self.max_steps + 1):
            print(f"\n【步骤 {step}】")
            
            # 构建消息
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                *self.history
            ]
            
            # 显示关键输入信息
            print(f"📝 输入消息数: {len(messages)} 条")
            print(f"📏 总字符数: {sum(len(m['content']) for m in messages)}")
            
            # 调用LLM
            response = call_llm(messages)
            print(f"🤖 LLM响应: {response[:100]}...")
            
            self.history.append({"role": "assistant", "content": response})
            
            if response.strip().startswith("So the final answer is:"):
                print(response)
                return self.results

            call = self.parse_function_call(response)
            
            if call:
                func_name = call["function"]
                params = call["parameters"]
                
                print(f"🔧 调用函数: {func_name}")
                print(f"📋 原始参数: {params}")
                
                # 处理参数引用
                self.process_parameters(params)
                print("📥 实际参数: " + json.dumps(params, ensure_ascii=False))
                
                # 执行函数
                result = execute_function(func_name, **params)
                self.results[func_name] = result
                self.trace.append({"function": func_name, "parameters": copy.deepcopy(params), "result": copy.deepcopy(result)})
                
                print("工具结果: " + json.dumps(result, ensure_ascii=False))
                
                # 反馈结果
                result_msg = f"Intermediate answer: {json.dumps(result, ensure_ascii=False)}"
                self.history.append({"role": "user", "content": result_msg})
                
            else:
                print("⚠️ 未识别到函数调用或结束标志")
                self.history.append({"role": "user", "content": "未识别到动作。请只返回 Follow up: 加函数与 parameters 对象，或在证据足够时给出最终答案标记。"})
        
        raise RuntimeError("达到调用上限，模型仍未给出最终结论。")

# ==================== 演示 ====================
def main():
    parser = argparse.ArgumentParser(description="手写 Self-Ask 工具循环")
    parser.add_argument("--count", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-steps", type=int, default=5)
    args = parser.parse_args()
    load_environment()
    if args.count <= 0 or args.max_steps < 1:
        parser.error("count 和 max-steps 必须大于0")
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")):
        raise SystemExit("请配置课程的 OPENAI_* 模型接口或 DASHSCOPE_API_KEY。")
    engine = SelfAskEngine(args.max_steps)
    
    task = grade_task(args.count, args.seed)
    started = perf_counter()
    error = None
    try:
        engine.run(task)
    except RuntimeError as failure:
        error = str(failure)
    validation = verify_trace(engine.trace, args.count, args.seed)
    report = {"task": task, "trace": engine.trace, "messages": engine.history,
              "validation": validation, "elapsed_seconds": perf_counter() - started,
              "stop_reason": "error_or_budget" if error else "final_answer", "error": error}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n独立数据流核对：" + json.dumps(validation, ensure_ascii=False, indent=2))
    print(f"运行耗时：{report['elapsed_seconds']:.3f} 秒；停止原因：{report['stop_reason']}")
    if error or not validation["passed"]:
        raise SystemExit(error or "实际数据与统计轨迹未通过独立核对。")


if __name__ == "__main__":
    main()
