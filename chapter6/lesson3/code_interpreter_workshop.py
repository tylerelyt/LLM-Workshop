#!/usr/bin/env python3
"""
Lesson 3: Code Interpreter Workshop

展示 AI 通过动态编写和执行代码来解决编程问题的能力。
"""

import os
from autogen import AssistantAgent, UserProxyAgent

def get_llm_config():
    """LLM 配置"""
    return {
        "config_list": [{
            "model": os.getenv("LLM_MODEL", "qwen-max"),
            "api_key": os.getenv("DASHSCOPE_API_KEY"),
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }],
        "temperature": 0.3,
    }

def create_code_interpreter():
    """创建通用的 Code Interpreter 系统"""
    assistant = AssistantAgent(
        name="Assistant",
        llm_config=get_llm_config(),
    )
    
    executor = UserProxyAgent(
        name="Executor", 
        human_input_mode="NEVER",
        max_consecutive_auto_reply=4,
        is_termination_msg=lambda msg: msg.get("content", "").strip().lower() in ["terminate", "exit", "done"],
        code_execution_config={"work_dir": "./workspace", "use_docker": False},
    )
    
    return assistant, executor

def main():
    """演示：Code Interpreter 解决编程问题"""
    print("🚀 Code Interpreter Workshop")
    print("="*40)
    
    # 创建通用 Code Interpreter
    assistant, executor = create_code_interpreter()
    
    # 具体任务定义
    task = """
给定以下物品列表，背包容量为10kg，求能获得的最大价值：

物品列表：
物品1: 重量2kg, 价值3元
物品2: 重量3kg, 价值4元  
物品3: 重量4kg, 价值5元
物品4: 重量5kg, 价值6元
物品5: 重量1kg, 价值2元

请找出最优的物品组合，使得总重量不超过10kg，且总价值最大。
"""
    
    print(f"📋 任务:\n{task}")
    print("\n🔄 开始执行...")
    print("-" * 30)
    
    # 执行任务
    os.makedirs("./workspace", exist_ok=True)
    executor.initiate_chat(assistant, message=task, max_turns=6)
    
    print("📁 输出保存在: ./workspace/")

if __name__ == "__main__":
    main()