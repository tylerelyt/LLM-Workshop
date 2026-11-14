#!/usr/bin/env python3
"""
持久记忆：MemGPT 风格的简化反思记忆演示

用本地 JSON 组织核心记忆、用户信息与反思模式，并在创建新智能体时注入系统消息。
这是 MemGPT 风格的教学实现，不依赖 MemGPT 服务或自动记忆检索。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import load_environment


import os
import argparse
from pathlib import Path
import json
import uuid
from datetime import datetime
from typing import Dict
from autogen import AssistantAgent

# ==================== MemGPT 风格的反思记忆系统 ====================
class MemGPTStyleReflectionAgent:
    """使用 MemGPT 风格简化的反思记忆智能体"""
    
    def __init__(self, name: str, role: str, memory_file: str = None):
        self.name = name
        self.role = role
        self.memory_file = memory_file or f"{name.lower()}_reflection_memory.json"
        
        # MemGPT 风格的记忆结构
        self.memory = {
            "core_memories": [],      # 核心反思经验
            "archival_memories": [],  # 详细的反思案例
            "human_info": {},         # 用户偏好和特征
            "reflection_patterns": [] # 反思模式和规律
        }
        self.load_memory()
        
        # 创建集成记忆的 AutoGen 智能体
        self.agent = self._create_memory_enhanced_agent()
    
    def _create_memory_enhanced_agent(self) -> AssistantAgent:
        """创建集成长期记忆的智能体"""
        llm_config = get_llm_config()
        
        # 构建包含记忆的系统消息
        memory_context = self._build_memory_context()
        self.initial_memory_context = memory_context
        
        system_message = f"""你是{self.role}，具有 MemGPT 风格的长期记忆能力。

{memory_context}

🧠 MemGPT 记忆系统：
- 本轮可用的历史信息仅限于上面实际加载的条目
- 基于历史经验提供个性化建议
- 持续学习和改进反思质量
- 建立长期的合作关系

请利用你的记忆提供更好的服务。"""
        
        return AssistantAgent(
            name=self.name,
            system_message=system_message,
            llm_config=llm_config
        )
    
    def _build_memory_context(self) -> str:
        """构建记忆上下文"""
        context = ""
        
        if self.memory["core_memories"]:
            context += "\n💡 核心反思经验:\n"
            for mem in self.memory["core_memories"][-5:]:
                context += f"- {mem['content']}\n"
        
        if self.memory["reflection_patterns"]:
            context += "\n📋 反思模式:\n"
            for pattern in self.memory["reflection_patterns"][-3:]:
                context += f"- {pattern['pattern']}: {pattern['description']}\n"
        
        if self.memory["human_info"]:
            context += "\n👤 用户特征:\n"
            for key, value in self.memory["human_info"].items():
                context += f"- {key}: {value}\n"
        
        return context
    
    def add_reflection_memory(self, content: str, memory_type: str = "core"):
        """添加反思记忆（MemGPT 风格）"""
        memory_entry = {
            "id": str(uuid.uuid4()),
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "importance": 7  # MemGPT 风格的重要性评分
        }
        
        if memory_type == "core":
            self.memory["core_memories"].append(memory_entry)
            # 保持记忆数量合理
            if len(self.memory["core_memories"]) > 15:
                self.memory["core_memories"] = self.memory["core_memories"][-15:]
        elif memory_type == "archival":
            self.memory["archival_memories"].append(memory_entry)
        
        self.save_memory()
    
    def add_reflection_pattern(self, pattern: str, description: str):
        """添加反思模式"""
        pattern_entry = {
            "pattern": pattern,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        self.memory["reflection_patterns"].append(pattern_entry)
        self.save_memory()
    
    def update_user_info(self, key: str, value: str):
        """更新用户信息"""
        self.memory["human_info"][key] = value
        self.save_memory()
    
    def save_memory(self):
        """保存记忆"""
        Path(self.memory_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)
    
    def load_memory(self):
        """加载记忆"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            except (ValueError, KeyError, TypeError) as e:
                raise ValueError(f"{self.name} 记忆格式无效，请保留原文件并使用新目录: {e}") from e

# ==================== 配置部分 ====================
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
        "temperature": 0.7,
    }

# ==================== 简化的反思系统 ====================
class SimplifiedReflectionSystem:
    """使用 MemGPT 风格简化的反思系统"""
    
    def __init__(self, memory_dir="."):
        directory = Path(memory_dir)
        self.actor = MemGPTStyleReflectionAgent("Actor", "内容创作专家", directory / "actor_reflection_memory.json")
        self.evaluator = MemGPTStyleReflectionAgent("Evaluator", "质量评估专家", directory / "evaluator_reflection_memory.json")
        self.reflector = MemGPTStyleReflectionAgent("Reflector", "反思分析专家", directory / "reflector_reflection_memory.json")
        

    def generate_with_memory_reflection(self, task: str) -> Dict:
        """使用 MemGPT 风格的记忆进行反思改进"""
        print(f"\n🧠 === MemGPT 风格的反思改进系统 ===")
        print(f"任务: {task[:100]}...")
        
        used_prior_memory = any(
            specialist.initial_memory_context.strip()
            for specialist in (self.actor, self.evaluator, self.reflector)
        )
        print("新建智能体实际注入的历史记忆：")
        for specialist in (self.actor, self.evaluator, self.reflector):
            context = specialist.initial_memory_context.strip()
            print(f"[{specialist.name}] {context[:450] or '无历史记忆'}")
            if len(context) > 450:
                print("…历史内容较长，可用 --output 保存完整 loaded_memory。")
            if specialist.memory["human_info"]:
                print(f"  实际注入的用户偏好：{specialist.memory['human_info']}")
        # 步骤1: Actor 基于记忆生成内容
        print("\n🎭 Actor 基于历史记忆生成内容...")
        initial_content = self._ask(self.actor.agent, f"请完成以下任务，利用你的历史记忆提供更好的内容：\n{task}")
        
        # 步骤2: Evaluator 基于记忆评估
        print("\n📊 Evaluator 基于历史经验评估...")
        evaluation = self._ask(self.evaluator.agent, f"请评估以下内容，基于你的历史评估经验：\n\n任务：{task}\n\n内容：\n{initial_content}")
        
        # 步骤3: Reflector 基于记忆深度反思
        print("\n🤔 Reflector 基于历史模式深度反思...")
        reflection = self._ask(self.reflector.agent, f"请基于你的反思经验分析以下内容的问题：\n\n内容：{initial_content}\n\n评估：{evaluation}")
        
        # 步骤4: 更新各智能体的记忆
        self._update_memories(task, initial_content, evaluation, reflection)
        
        # 步骤5: Actor 基于反思改进内容
        print("\n🔄 Actor 基于反思改进内容...")
        improved_content = self._ask(self.actor.agent, f"请基于以下反思改进内容：\n\n原内容：{initial_content}\n\n反思：{reflection}")
        
        return {
            "task": task,
            "initial_content": initial_content,
            "evaluation": evaluation,
            "reflection": reflection,
            "improved_content": improved_content,
            "memory_enhanced": used_prior_memory,
            "loaded_memory": {specialist.name: specialist.initial_memory_context
                              for specialist in (self.actor, self.evaluator, self.reflector)}
        }
    
    def _ask(self, agent, prompt: str) -> str:
        ok, answer = agent.generate_oai_reply(messages=[{"role": "user", "content": prompt}])
        if isinstance(answer, dict):
            answer = answer.get("content")
        if not ok:
            raise RuntimeError(f"{agent.name} 未完成模型调用。")
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(f"{agent.name} 没有返回可用内容。")
        return answer.strip()

    def _update_memories(self, task: str, content: str, evaluation: str, reflection: str):
        """更新各智能体的记忆"""
        # Actor 记忆
        self.actor.add_reflection_memory(f"上次任务约束：{task}")
        self.actor.add_reflection_memory(f"上次改进建议：{reflection}")
        self.actor.update_user_info("最近任务类型", task.split("：")[0] if "：" in task else "通用")
        
        # Evaluator 记忆
        self.evaluator.add_reflection_memory(f"上次实际评估：{evaluation}")
        self.evaluator.add_reflection_pattern("质量评估", "从多维度系统性评估内容")
        
        # Reflector 记忆
        self.reflector.add_reflection_memory(f"上次实际反思：{reflection}")
        self.reflector.add_reflection_pattern("深度分析", "识别内容不足并提供改进建议")
        
        print("🧠 所有智能体记忆已更新")

# ==================== 演示程序 ====================
def show_memory_result(result):
    import difflib
    import textwrap
    def excerpt(text, limit=500):
        return text if len(text) <= limit else text[:limit] + "\n…内容较长，使用 --output 保存完整内容。"
    print("\n=== 本轮实际回答与改进 ===")
    actor_memory = bool(result["loaded_memory"].get("Actor", "").strip())
    label = "Actor 已注入历史记忆" if actor_memory else "Actor 无历史记忆"
    print(f"本轮首次回答（{label}）：\n" + excerpt(result["initial_content"]))
    print("本轮评估：\n" + excerpt(result["evaluation"]))
    print("本轮反思：\n" + excerpt(result["reflection"]))
    def lines(content):
        return [line for paragraph in content.splitlines() for line in (textwrap.wrap(paragraph, 44) or [""])]
    changes = list(difflib.unified_diff(lines(result["initial_content"]), lines(result["improved_content"]),
                                      fromfile="本轮首次回答", tofile="本轮改稿", lineterm="", n=1))
    print("本轮改稿差异（最多 36 行）：")
    print("\n".join(changes[:36]) if changes else "内容没有变化。")
    if len(changes) > 36:
        print("…差异较长，可用 --output 保存完整改稿。")
    print("跨会话核对：在上面的历史条目和首次回答中找出同一约束；本轮改稿变化不能证明历史记忆有效。")


def demo_simplified_reflection(memory_dir="."):
    """演示简化的反思系统"""
    print("\n📝 === MemGPT 风格反思系统演示 ===")
    
    system = SimplifiedReflectionSystem(memory_dir)
    
    # 测试任务
    task = """设计一个智能家居控制系统，要求：
- 支持语音控制和手机APP控制
- 集成温度、湿度、光照传感器
- 具备学习用户习惯的AI功能
- 确保数据安全和隐私保护
- 提供节能优化建议"""
    
    try:
        result = system.generate_with_memory_reflection(task)
        
        show_memory_result(result)
        print(f"本轮是否读取历史记忆: {'是' if result['memory_enhanced'] else '否'}")
        
        return result
        
    except Exception as e:
        print(f"❌ 演示出现错误: {e}")
        return None

def main():
    """主程序"""
    parser = argparse.ArgumentParser(description="验证新进程如何加载本地持久记忆")
    parser.add_argument("--memory-dir", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print("🧠 === MemGPT 简化反思记忆演示 ===")
    print("检查新会话注入的历史约束，以及本轮回答的实际内容")
    print("="*60)
    
    # 环境检查
    try:
        llm_config = get_llm_config()
        print("✅ LLM 配置检查通过")
    except ValueError as e:
        raise SystemExit(f"❌ {e}") from None
    
    try:
        # 运行演示
        result = demo_simplified_reflection(args.memory_dir)
        if result is None:
            raise SystemExit(1)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n" + "="*60)
        print("🎉 === MemGPT 简化演示完成 ===")
        
        print("本练习用 JSON 保存数据，在新建智能体时选择最近的核心记忆与模式加入系统消息。")
        print("归档内容不会自动检索；文件读入也不证明本次回答已正确使用经验。")
        print("请对照 loaded_memory 和回答中的实际约束，判断是否采用了相关记录。")
        print(f"记忆目录: {args.memory_dir}")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()
