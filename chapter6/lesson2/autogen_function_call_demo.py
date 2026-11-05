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
import json
import random
from typing import Annotated
from autogen import AssistantAgent, UserProxyAgent, register_function

# ==================== LLM 配置 ====================
def get_llm_config():
    """获取 LLM 配置"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")
    
    return {
        "config_list": [{
            "model": os.getenv("LLM_MODEL", "qwen-max"),
            "api_key": api_key,
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }],
        "temperature": 0.3,
    }

# ==================== AutoGen 函数定义 ====================
# 注意：这些函数与 lesson1 完全相同，但为 AutoGen 添加了类型注解

def generate_numbers(
    count: Annotated[int, "生成数字的数量"] = 10,
    min_val: Annotated[int, "最小值"] = 1,
    max_val: Annotated[int, "最大值"] = 100,
    seed: Annotated[int, "随机种子，用于保证结果可重复性"] = None
) -> Annotated[dict, "包含生成的数字列表和描述信息"]:
    """
    生成随机数列表 - 通用的随机数生成函数
    AutoGen 通过类型注解自动处理参数验证和文档生成
    """
    print(f"🎲 [AutoGen] 生成 {count} 个范围在 [{min_val}, {max_val}] 的随机数...")
    
    if seed is not None:
        random.seed(seed)
    numbers = [random.randint(min_val, max_val) for _ in range(count)]
    
    result = {
        "description": f"生成 {count} 个随机数",
        "count": count,
        "numbers": numbers
    }
    
    print(f"✅ [AutoGen] 数字生成完成: {numbers}")
    return result

def calculate_stats(
    numbers: Annotated[list, "数字列表"],
    operation: Annotated[str, "操作类型: sum/avg/max/min/all"] = "all"
) -> Annotated[dict, "统计计算结果"]:
    """
    计算统计信息 - 与 lesson1 相同的函数，但添加了 AutoGen 类型注解
    AutoGen 通过类型注解自动处理参数验证和函数调用
    """
    print(f"🔢 [AutoGen] 计算统计信息，操作类型: {operation}")
    
    try:
        # AutoGen 会自动处理类型转换，但我们保持兼容性
        if isinstance(numbers, str):
            numbers = json.loads(numbers)
        
        numbers = [float(x) for x in numbers]
        result = {"count": len(numbers)}
        
        if operation in ["sum", "all"]:
            result["sum"] = sum(numbers)
        if operation in ["avg", "all"]:
            result["average"] = sum(numbers) / len(numbers)
        if operation in ["max", "all"]:
            result["maximum"] = max(numbers)
        if operation in ["min", "all"]:
            result["minimum"] = min(numbers)
        if operation == "all":
            sorted_nums = sorted(numbers)
            n = len(numbers)
            result["median"] = (sorted_nums[n//2-1] + sorted_nums[n//2]) / 2 if n % 2 == 0 else sorted_nums[n//2]
        
        print(f"✅ [AutoGen] 统计计算完成")
        return result
        
    except Exception as e:
        print(f"❌ [AutoGen] 统计计算失败: {e}")
        return {"error": f"统计计算失败: {str(e)}"}

# ==================== AutoGen 智能体设置 ====================
def create_assistant_agent():
    """创建通用智能助手 - 对应 lesson1 的 SelfAskEngine"""
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
        termination_keywords = ["完成", "结束", "任务完成", "分析完成"]
    
    return UserProxyAgent(
        name="用户代理",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=8,
        is_termination_msg=lambda msg: any(word in msg.get("content", "").lower() 
                                         for word in termination_keywords),
        code_execution_config={"use_docker": False},
    )

# ==================== 演示主程序 ====================
def main():
    """主演示函数"""
    print("🤖 === AutoGen Function Call Demo ===")
    print("与 Lesson1 相同的任务，体验 AutoGen 框架的简化效果")
    print("="*60)
    
    # 环境检查
    try:
        llm_config = get_llm_config()
        print("✅ LLM 配置检查通过")
    except ValueError as e:
        print(f"❌ {e}")
        return
    
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
    
    # 相同的测试任务（与 lesson1 完全一致），为了结果可重复性，指定随机种子
    task = """请帮我生成一组测试数据并评估它是否适合作为学生考试成绩的样本。要求数据量15-20个，分数范围0-100，使用随机种子42以确保结果可重复。如果平均分在60-80之间且最低分不低于30，就算合格的样本。请告诉我最终结论：合格还是不合格？"""
    
    print(f"\n🎯 测试任务: {task}")
    print("="*60)
    
    try:
        # 启动 AutoGen 对话 - 框架自动处理所有复杂逻辑
        print("🚀 启动 AutoGen 自动化流程...")
        user_proxy.initiate_chat(
            assistant,
            message=task,
            max_turns=10
        )
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    main()