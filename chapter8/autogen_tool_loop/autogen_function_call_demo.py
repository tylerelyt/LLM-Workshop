#!/usr/bin/env python3
"""
Chapter 6 Lesson 2: AutoGen Function Call Demo
使用 AutoGen 框架实现 Function Call，对比手动实现的差异

核心学习目标：
1. 体验 AutoGen 如何简化 Function Call 开发
2. 对比相同任务在两种实现方式下的差异
3. 理解框架带来的开发效率提升
"""

import os
import argparse
import sys
from pathlib import Path
import json
import random
from typing import Annotated
from autogen import AssistantAgent, UserProxyAgent, register_function
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chapter8.manual_tool_loop.function_call_workshop import (
    generate_numbers as generate_data, calculate_stats as compute_stats, grade_task,
)

from copy import deepcopy
from time import perf_counter
from workshop_runtime.deepseek import load_environment
from chapter8.manual_tool_loop.verification import verify_trace

EXECUTION_TRACE = []

# ==================== LLM 配置 ====================
def get_llm_config():
    """获取 LLM 配置"""
    load_environment()
    compatible = bool(os.getenv("OPENAI_API_KEY"))
    api_key = os.getenv("OPENAI_API_KEY") if compatible else os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请配置 OPENAI_API_KEY 和 OPENAI_MODEL，或设置 DASHSCOPE_API_KEY。")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini") if compatible else os.getenv("LLM_MODEL", "qwen-max")
    base_url = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1") if compatible else "https://dashscope.aliyuncs.com/compatible-mode/v1"

    return {
        "config_list": [{
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
        }],
        "temperature": 0.3,
    }

# ==================== AutoGen 函数定义 ====================
# 注意：这些函数与 手写函数调用练习 完全相同，但为 AutoGen 添加了类型注解

def generate_numbers(
    count: Annotated[int, "生成数字的数量"] = 10,
    min_val: Annotated[int, "最小值"] = 1,
    max_val: Annotated[int, "最大值"] = 100,
    seed: Annotated[int | None, "随机种子，用于保证结果可重复性"] = None
) -> Annotated[dict, "包含生成的数字列表和描述信息"]:
    """
    生成随机数列表 - 通用的随机数生成函数
    AutoGen 通过类型注解自动处理参数验证和文档生成
    """
    print(f"🎲 [AutoGen] 生成 {count} 个范围在 [{min_val}, {max_val}] 的随机数...")
    
    try:
        result = generate_data(count, min_val, max_val, seed)
    except (TypeError, ValueError) as error:
        result = {"error": str(error)}
    EXECUTION_TRACE.append({"function": "generate_numbers", "parameters": {"count": count, "min_val": min_val, "max_val": max_val, "seed": seed}, "result": deepcopy(result)})
    numbers = result.get("numbers")
    print(f"[AutoGen] 实际生成结果: {result}")
    return result

def calculate_stats(
    numbers: Annotated[list, "数字列表"],
    operation: Annotated[str, "操作类型: sum/avg/max/min/all"] = "all"
) -> Annotated[dict, "统计计算结果"]:
    """
    计算统计信息 - 与 手写函数调用练习 相同的函数，但添加了 AutoGen 类型注解
    AutoGen 通过类型注解自动处理参数验证和函数调用
    """
    print(f"🔢 [AutoGen] 计算统计信息，操作类型: {operation}")
    
    try:
        result = compute_stats(numbers, operation)
        print("实际统计结果: " + json.dumps(result, ensure_ascii=False))
    except (TypeError, ValueError) as error:
        result = {"error": str(error)}
    EXECUTION_TRACE.append({"function": "calculate_stats", "parameters": {"numbers": deepcopy(numbers), "operation": operation}, "result": deepcopy(result)})
    return result

# ==================== AutoGen 智能体设置 ====================
def create_assistant_agent():
    """创建通用智能助手 - 对应 手写函数调用练习 的 SelfAskEngine"""
    llm_config = get_llm_config()
    
    return AssistantAgent(
        name="智能助手",
        llm_config=llm_config,
    )

def create_user_proxy(termination_keywords=None):
    """
    创建用户代理 - 处理函数执行
    
    Args:
        termination_keywords: 用于判断对话结束的关键词列表，默认使用通用关键词
    """
    if termination_keywords is None:
        termination_keywords = ["TERMINATE"]
    
    return UserProxyAgent(
        name="用户代理",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=8,
        is_termination_msg=lambda msg: not msg.get("tool_calls") and not msg.get("function_call") and any(
            (msg.get("content") or "").strip().lower().endswith(word.lower()) for word in termination_keywords),
        code_execution_config=False,
    )

# ==================== 演示主程序 ====================
def main():
    """主演示函数"""
    parser = argparse.ArgumentParser(description="与手写版本对照的框架工具循环")
    parser.add_argument("--count", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-steps", type=int, default=10, help="框架对话轮次上限，单位与手写循环不同")
    args = parser.parse_args()
    load_environment()
    EXECUTION_TRACE.clear()
    if args.count <= 0 or args.max_steps < 1: parser.error("count 和 max-steps 必须大于0")
    print("🤖 === AutoGen Function Call Demo ===")
    print("与手写循环使用相同任务、工具和业务核对标准")
    print("="*60)
    
    # 环境检查
    try:
        llm_config = get_llm_config()
        print("✅ LLM 配置检查通过")
    except ValueError as e:
        raise SystemExit(str(e)) from e
    
    # 创建智能体
    print("\n🔧 创建 AutoGen 智能体...")
    assistant = create_assistant_agent()
    user_proxy = create_user_proxy()
    
    # 注册函数 - AutoGen 的简化方式
    print("📝 注册函数到 AutoGen 框架...")
    register_function(
        generate_numbers,
        caller=assistant,
        executor=user_proxy,
        name="generate_numbers",
        description="生成指定数量和范围的随机数列表"
    )
    
    register_function(
        calculate_stats,
        caller=assistant,
        executor=user_proxy,
        name="calculate_stats",
        description="计算数字列表的统计信息"
    )
    
    print("✅ AutoGen 函数注册完成")
    
    # 相同的测试任务（与 手写函数调用练习 完全一致），为了结果可重复性，指定随机种子
    task = grade_task(args.count, args.seed) + "完成结论后单独输出 TERMINATE。"
    print(f"\n🎯 测试任务: {task}")
    print("="*60)
    
    started = perf_counter()
    try:
        # 启动 AutoGen 对话 - 框架自动处理所有复杂逻辑
        print("🚀 启动 AutoGen 自动化流程...")
        result = user_proxy.initiate_chat(
            assistant,
            message=task,
            max_turns=args.max_steps
        )
        validation = verify_trace(EXECUTION_TRACE, args.count, args.seed)
        report = {"task": task, "messages": result.chat_history, "trace": EXECUTION_TRACE,
                  "validation": validation, "elapsed_seconds": perf_counter() - started}
        print("独立数据流核对：" + json.dumps(validation, ensure_ascii=False, indent=2))
        print(f"运行耗时：{report['elapsed_seconds']:.3f} 秒")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        if not validation["passed"]:
            raise RuntimeError("框架返回了回答，但实际工具数据流未通过独立核对。")
    except Exception as e:
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"task": task, "trace": EXECUTION_TRACE, "validation": verify_trace(EXECUTION_TRACE, args.count, args.seed), "error": str(e), "elapsed_seconds": perf_counter() - started}, ensure_ascii=False, indent=2))
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()