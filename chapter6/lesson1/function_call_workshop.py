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
import json
import random
from datetime import datetime
from openai import OpenAI

# ==================== LLM 调用 ====================
def call_llm(messages, model="qwen-max"):
    """调用 LLM"""
    try:
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM调用失败: {str(e)}"

# ==================== 工具函数 ====================
def generate_numbers(count=10, min_val=1, max_val=100, seed=None):
    """生成随机数列表"""
    if seed is not None:
        random.seed(seed)
    numbers = [random.randint(min_val, max_val) for _ in range(count)]
    return {
        "description": f"生成 {count} 个随机数",
        "count": count,
        "numbers": numbers
    }

def calculate_stats(numbers, operation="all"):
    """计算统计信息"""
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
    
    return result

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
    """执行函数"""
    if name in FUNCTIONS:
        return FUNCTIONS[name]["func"](**params)
    return {"error": f"未知函数: {name}"}

# ==================== Self-Ask 引擎 ====================
class SelfAskEngine:
    def __init__(self):
        self.history = []
        self.results = {}
    
    def get_system_prompt(self):
        """系统提示词"""
        return f"""严格按照 self-ask 格式回复。每次必须以 "Follow up:" 开始，后跟函数调用JSON。

可用函数：
{get_function_descriptions()}

格式示例：
Question: 帮我查询今天北京的天气情况并翻译成英文
Follow up: {{"action": "call_function", "function": "get_weather", "parameters": {{"city": "北京", "date": "today"}}}}
Intermediate answer: {{"city": "北京", "temperature": "15°C", "weather": "多云", "humidity": "60%"}}
Follow up: {{"action": "call_function", "function": "translate_text", "parameters": {{"text": "北京今天多云，温度15度", "target_lang": "en"}}}}
Intermediate answer: {{"original": "北京今天多云，温度15度", "translated": "Beijing is cloudy today with a temperature of 15 degrees", "language": "en"}}
So the final answer is: 北京今天的天气是多云，温度15°C，湿度60%。英文翻译：Beijing is cloudy today with a temperature of 15 degrees.

规则：
1. 必须以 "Follow up:" 开始回复
2. 完成时用 "So the final answer is:" 结束
3. 不要添加其他解释文字"""

    def parse_function_call(self, response):
        """解析函数调用"""
        if "Follow up:" not in response:
            return None
            
        start = response.find("Follow up:") + len("Follow up:")
        json_start = response.find("{", start)
        
        if json_start == -1:
            return None
            
        # 括号匹配找到完整JSON
        brace_count = 0
        json_end = json_start
        for i in range(json_start, len(response)):
            if response[i] == '{':
                brace_count += 1
            elif response[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        try:
            json_str = response[json_start:json_end]
            call = json.loads(json_str)
            return call if "function" in call else None
        except:
            return None

    def process_parameters(self, params):
        """处理参数中的数据引用 - 通用的结果引用处理"""
        for key, value in params.items():
            # 通用的数据引用处理
            if isinstance(value, str) and len(value) < 50:
                # 检查是否有匹配的结果数据
                for func_name, result in self.results.items():
                    if isinstance(result, dict) and "error" not in result:
                        # 如果参数名与结果中的某个键匹配，使用该数据
                        if key in result:
                            params[key] = result[key]
                            break
                        # 如果参数值提到了某个函数名，尝试使用该函数的结果
                        elif func_name in value.lower():
                            # 优先使用与参数名匹配的键
                            if key in result:
                                params[key] = result[key]
                            # 否则使用整个结果
                            elif isinstance(result, (list, dict)):
                                params[key] = result
                            break

    def run(self, request):
        """执行完整流程"""
        print(f"🎯 任务: {request}")
        print("="*50)
        
        self.history.append({"role": "user", "content": request})
        
        for step in range(1, 6):  # 最多5步
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
            
            # 解析函数调用
            call = self.parse_function_call(response)
            
            if call:
                func_name = call["function"]
                params = call["parameters"]
                
                print(f"🔧 调用函数: {func_name}")
                print(f"📋 参数: {params}")
                
                # 处理参数引用
                self.process_parameters(params)
                
                # 执行函数
                result = execute_function(func_name, **params)
                self.results[func_name] = result
                
                print(f"✅ 结果: {str(result)[:100]}...")
                
                # 反馈结果
                result_msg = f"Intermediate answer: {json.dumps(result, ensure_ascii=False)}"
                self.history.append({"role": "user", "content": result_msg})
                
            elif "So the final answer is:" in response:
                print("🎉 任务完成!")
                break
            else:
                print("⚠️ 未识别到函数调用或结束标志")
        
        return self.results

# ==================== 演示 ====================
def main():
    print("🚀 Function Call Workshop")
    print("学习目标: 理解 LLM 自主调用函数的核心机制\n")
    
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ 请设置环境变量: export DASHSCOPE_API_KEY='your-key'")
        return
    
    engine = SelfAskEngine()
    
    # 测试任务 - 为了结果可重复性，指定随机种子
    task = """请帮我生成一组测试数据并评估它是否适合作为学生考试成绩的样本。要求数据量15-20个，分数范围0-100，使用随机种子42确保结果可重复。如果平均分在60-80之间且最低分不低于30，就算合格的样本。请告诉我最终结论：合格还是不合格？"""
    
    results = engine.run(task)
    
    print("\n" + "="*50)
    print("📊 执行总结:")
    for func, result in results.items():
        if "error" not in result:
            print(f"✅ {func}: 成功")
        else:
            print(f"❌ {func}: {result['error']}")
    
    print("\n🎓 核心学习点:")
    print("• Self-Ask 格式: Follow up → Intermediate answer → Final answer")
    print("• 函数注册: 告诉LLM有哪些工具可用")  
    print("• 任务分解: LLM自主将复杂任务分解为步骤")
    print("• 数据传递: 函数间通过对话历史传递数据")

if __name__ == "__main__":
    main()
