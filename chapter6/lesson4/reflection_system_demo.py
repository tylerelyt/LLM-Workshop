#!/usr/bin/env python3
"""
Lesson 4: 反思改进系统演示

展示如何构建基于反思的内容改进系统，通过多智能体协作实现：
1. 内容生成和质量分析
2. 系统性发现遗漏点
3. 基于反思的内容改进
4. 长期记忆和经验积累

基于 AutoGen 的真实实现，支持语义检索的遗漏点记忆系统。
"""

import argparse
import json
import os
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from autogen import AssistantAgent, UserProxyAgent

# ==================== 配置部分 ====================
def get_llm_config():
    """获取 LLM 配置"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")
    
    model = os.getenv("LLM_MODEL", "qwen-max")
    return {
        "config_list": [{
            "model": model,
            "api_key": api_key,
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }],
        "temperature": 0.7,
    }

# ==================== 遗漏点记忆系统 ====================
class OmissionMemory:
    """遗漏点长期记忆系统（扁平存储）。

    - 持久化到脚本同目录 JSON 文件 `reflection_memory.json`
    - 仅语义检索（DashScope 兼容 OpenAI 接口）。不可用则不检索（返回空）
    - 存储结构为扁平列表：每条为一个反思条目（不再按领域分层）。
    """

    def __init__(self, memory_file: str = None) -> None:
        # 将持久化文件固定在脚本目录，避免工作目录变化导致丢失
        default_path = os.path.join(os.path.dirname(__file__), "reflection_memory.json")
        self.memory_file = memory_file or default_path
        self.entries: List[Dict] = []
        self.embeddings: Dict[str, np.ndarray] = {}
        self._embedding_client = self._init_embedding_client()
        self.load_memory()

    def _init_embedding_client(self):
        try:
            import openai  # type: ignore

            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                return None

            # 使用 DashScope 兼容模式
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            return client
        except Exception:
            return None

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        if not self._embedding_client:
            return None
        try:
            resp = self._embedding_client.embeddings.create(
                model="text-embedding-v1", input=text
            )
            return np.array(resp.data[0].embedding)
        except Exception:
            return None

    def _text_for_embedding(self, item: Dict) -> str:
        parts = [
            item.get("domain", ""),
            item.get("type", ""),
            item.get("description", ""),
            item.get("suggestion", ""),
        ]
        return " ".join([p for p in parts if p])

    def add_omissions(self, domain: str, omissions: List[Dict]) -> None:
        for omission in omissions:
            entry = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "domain": domain,
                "type": omission.get("type", ""),
                "description": omission.get("description", ""),
                "suggestion": omission.get("suggestion", ""),
            }
            self.entries.append(entry)

            emb_text = self._text_for_embedding(entry)
            emb = self._get_embedding(emb_text)
            if emb is not None:
                self.embeddings[entry["id"]] = emb

        self.save_memory()
        print(f"💾 已保存 {len(omissions)} 个遗漏点到领域：{domain}")

    def get_relevant_omissions(self, query: str, limit: int = 3) -> List[Dict]:
        if not self.entries:
            return []

        # 仅语义召回（若 embeddings 缺失则懒加载计算）
        query_emb = self._get_embedding(query)
        if query_emb is None:
            return []

        scored: List[Tuple[float, Dict]] = []
        for item in self.entries:
            emb = self.embeddings.get(item["id"])  # type: ignore[index]
            if emb is None:
                # 懒加载为该条记忆生成嵌入
                text = self._text_for_embedding(item)
                emb = self._get_embedding(text)
                if emb is None:
                    continue
                self.embeddings[item["id"]] = emb  # type: ignore[index]
            sim = float(np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb)))
            scored.append((sim, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def save_memory(self) -> None:
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_memory(self) -> None:
        if not os.path.exists(self.memory_file):
            return
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 新版仅支持扁平列表
            self.entries = data if isinstance(data, list) else []
        except Exception:
            self.entries = []

# 全局记忆系统实例
memory = OmissionMemory()

# ==================== 反思消息处理 ====================
def _reflection_message(recipient, messages, sender, config):
    content = recipient.chat_messages_for_summary(sender)[-1]["content"]

    # 在反思前检索相关历史反思，作为上下文提示
    relevant = memory.get_relevant_omissions(content)
    hints = ""
    if relevant:
        lines = [f"• {it.get('description', '')}（建议：{it.get('suggestion', '')}）" for it in relevant]
        hints = "\n历史遗漏点参考:\n" + "\n".join(lines)

    return f"""请分析以下内容的遗漏点：

{content}
{hints}

请以JSON格式输出遗漏点分析：
```json
{{
  "domain": "内容主题领域（自动识别）",
  "omissions": [
    {{
      "type": "遗漏类型",
      "description": "具体遗漏描述",
      "suggestion": "改进建议"
    }}
  ]
}}
```"""

def _extract_omissions_from_reflection(reflection_text: str) -> Tuple[str, List[Dict]]:
    try:
        match = re.search(r"```json\s*(\{.*?\})\s*```", reflection_text, re.DOTALL)
        if not match:
            return "通用", []
        data = json.loads(match.group(1))
        domain = data.get("domain", "通用")
        omissions = data.get("omissions", [])
        if isinstance(omissions, list):
            return domain, omissions
        return domain, []
    except Exception:
        return "通用", []

# ==================== 智能体创建 ====================
def create_actor():
    """创建Actor智能体 - 负责内容生成和行动执行"""
    llm_config = get_llm_config()
    
    return AssistantAgent(
        name="Actor",
        system_message="""你是内容创作专家，负责根据用户需求生成高质量内容。

请根据要求创作内容，力求全面和深入。""",
        llm_config=llm_config,
    )

def create_evaluator():
    """创建Evaluator智能体 - 负责评估内容质量"""
    llm_config = get_llm_config()
    
    return AssistantAgent(
        name="Evaluator",
        system_message="""你是内容质量评估专家，负责评估内容的各个方面。

请客观评估内容质量，提供详细的评估报告。""",
        llm_config=llm_config,
    )

def create_self_reflection():
    """创建Self-reflection智能体 - 负责深度反思和学习"""
    llm_config = get_llm_config()
    
    return AssistantAgent(
        name="Self-reflection",
        system_message="""你是深度反思专家，负责基于评估结果进行深度反思和学习。

请以JSON格式输出反思结果：
```json
{
    "domain": "内容主题领域",
    "omissions": [
        {
            "type": "遗漏类型",
            "description": "具体遗漏描述",
            "suggestion": "改进建议"
        }
    ],
    "lessons_learned": ["经验教训1", "经验教训2"],
    "improvement_plan": "具体的改进计划"
}
```""",
        llm_config=llm_config,
    )

def create_user_proxy():
    """创建用户代理"""
    return UserProxyAgent(
        name="用户",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=2,
        is_termination_msg=lambda msg: "改进完成" in msg.get("content", "").lower(),
        code_execution_config={"use_docker": False},
    )

# ==================== 反思改进流程 ====================
class ReflectionSystem:
    """反思改进系统 - 基于标准反思学习架构"""
    
    def __init__(self):
        # 按照反思学习架构创建智能体
        self.actor = create_actor()           # Actor: 负责内容生成和行动执行
        self.evaluator = create_evaluator()   # Evaluator: 负责评估内容质量
        self.self_reflection = create_self_reflection()  # Self-reflection: 负责深度反思
        self.user_proxy = create_user_proxy()  # 用户代理：协调整个流程
    
    def generate_with_reflection(self, task: str) -> Dict:
        """完整的反思改进流程"""
        print(f"\n🎯 开始反思改进流程")
        print("="*60)
        
        # 第一步：检索历史经验并加载到Actor
        print("\n📚 步骤1: 加载历史反思经验...")
        historical_experience = memory.get_relevant_omissions(task)
        
        experience_context = ""
        if historical_experience:
            print(f"找到 {len(historical_experience)} 条相关经验")
            experience_context = "\n\n📖 历史反思经验参考：\n"
            for exp in historical_experience:
                experience_context += f"- 主题: {exp.get('domain', 'N/A')}\n"
                experience_context += f"  💡 {exp.get('description', 'N/A')}（建议：{exp.get('suggestion', 'N/A')}）\n"
        else:
            print("未找到相关历史经验，进行首次探索")
        
        # 第二步：Actor生成初始内容（已加载历史经验）
        print("\n🎭 步骤2: Actor生成初始内容...")
        generation_prompt = f"""请完成以下任务：

{task}

{experience_context}

请创作结构完整、内容丰富的回答。"""
        
        self.user_proxy.initiate_chat(
            self.actor,
            message=generation_prompt,
            max_turns=2
        )
        
        # 获取生成的内容
        generated_content = self._extract_content_from_chat()
        print(f"✅ 初始内容生成完成 ({len(generated_content)} 字符)")
        
        # 第三步：Evaluator评估内容质量
        print("\n📊 步骤3: Evaluator评估内容质量...")
        evaluation_prompt = f"""请评估以下内容的质量：

任务：{task}

内容：
{generated_content}

请从完整性、逻辑性、实用性、前瞻性、受众适配等维度进行全面评估。"""
        
        self.user_proxy.initiate_chat(
            self.evaluator,
            message=evaluation_prompt,
            max_turns=2
        )
        
        # 获取评估结果
        evaluation_result = self._extract_content_from_chat()
        print("✅ 内容评估完成")
        
        # 第四步：Self-reflection深度反思
        print("\n🧠 步骤4: Self-reflection深度反思...")
        reflection_prompt = f"""基于评估结果，请进行深度反思：

原始内容：
{generated_content}

评估结果：
{evaluation_result}

请深入分析内容中的问题和不足，提取经验教训，并提供具体的改进建议。"""
        
        self.user_proxy.initiate_chat(
            self.self_reflection,
            message=reflection_prompt,
            max_turns=2
        )
        
        # 解析反思结果
        reflection_result = self._extract_analysis_from_chat()
        print("✅ 深度反思完成")
        
        # 第五步：基于反思结果改进内容
        if reflection_result.get("omissions"):
            print(f"\n🔄 步骤5: 基于反思结果改进内容 (发现 {len(reflection_result['omissions'])} 个改进点)...")
            
            improvement_prompt = f"""基于反思结果，请重新优化内容：

原始内容：
{generated_content}

反思结果：
{json.dumps(reflection_result, ensure_ascii=False, indent=2)}

请生成改进后的完整内容，确保解决反思中发现的遗漏点。"""
            
            self.user_proxy.initiate_chat(
                self.actor,
                message=improvement_prompt,
                max_turns=2
            )
            
            improved_content = self._extract_content_from_chat()
            print("✅ 内容改进完成")
        else:
            print("\n✅ 内容质量良好，无需改进")
            improved_content = generated_content
        
        # 第六步：保存反思经验到长期记忆
        print("\n💾 步骤6: 保存反思经验到长期记忆...")
        if reflection_result.get("omissions"):
            # 转换格式以适配记忆系统
            omissions_for_memory = []
            for omission in reflection_result["omissions"]:
                omissions_for_memory.append({
                    "type": omission.get("type", "通用"),
                    "description": omission.get("description", ""),
                    "suggestion": omission.get("suggestion", "")
                })
            # 使用任务内容的前50个字符作为domain
            domain = task[:50] + "..." if len(task) > 50 else task
            memory.add_omissions(domain, omissions_for_memory)
            print(f"✅ 已保存 {len(omissions_for_memory)} 个遗漏点到长期记忆")
        else:
            print("ℹ️ 未发现遗漏点，无需保存")
        
        # 返回结果
        result = {
            "task": task,
            "original_content": generated_content,
            "improved_content": improved_content,
            "evaluation": evaluation_result,
            "reflection": reflection_result,
            "improvement_applied": len(reflection_result.get("omissions", [])) > 0
        }
        
        print("\n🎉 反思改进流程完成！")
        return result
    
    def _extract_content_from_chat(self) -> str:
        """从对话中提取内容"""
        try:
            # 获取最后一条助手消息
            if hasattr(self.user_proxy, 'chat_messages'):
                for agent_name, messages in self.user_proxy.chat_messages.items():
                    if messages and agent_name != "用户":
                        last_message = messages[-1]
                        if isinstance(last_message, dict):
                            return last_message.get("content", "")
                        else:
                            return str(last_message)
            return "内容提取失败"
        except Exception as e:
            print(f"⚠️ 内容提取错误: {e}")
            return "内容提取失败"
    
    def _extract_analysis_from_chat(self) -> Dict:
        """从对话中提取分析结果"""
        try:
            # 专门从Self-reflection的消息中提取内容
            if hasattr(self.user_proxy, 'chat_messages') and "Self-reflection" in self.user_proxy.chat_messages:
                messages = self.user_proxy.chat_messages["Self-reflection"]
                if messages:
                    content = messages[-1].get("content", "") if isinstance(messages[-1], dict) else str(messages[-1])
                    print(f"🔍 提取的反思内容: {content[:200]}...")
                    
                    # 尝试从内容中提取JSON
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        print(f"📋 找到JSON内容: {json_str[:100]}...")
                        result = json.loads(json_str)
                        print(f"✅ JSON解析成功，遗漏点数量: {len(result.get('omissions', []))}")
                        return result
                    else:
                        print("⚠️ 未找到JSON格式的反思结果")
                        # 如果没有找到JSON，创建基本的结构
                        return {
                            "domain": "通用",
                            "omissions": [],
                            "lessons_learned": [],
                            "improvement_plan": ""
                        }
            else:
                print("⚠️ 未找到Self-reflection的消息")
                # 尝试从所有消息中查找包含JSON的内容
                if hasattr(self.user_proxy, 'chat_messages'):
                    for agent_name, messages in self.user_proxy.chat_messages.items():
                        for msg in messages[::-1]:  # 从最新的消息开始查找
                            content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
                            if "```json" in content:
                                print(f"🔍 在 {agent_name} 的消息中找到JSON内容")
                                import re
                                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                                if json_match:
                                    json_str = json_match.group(1)
                                    print(f"📋 找到JSON内容: {json_str[:100]}...")
                                    result = json.loads(json_str)
                                    print(f"✅ JSON解析成功，遗漏点数量: {len(result.get('omissions', []))}")
                                    return result
                
                return {
                    "domain": "通用",
                    "omissions": [],
                    "lessons_learned": [],
                    "improvement_plan": ""
                }
        except Exception as e:
            print(f"⚠️ 反思结果解析错误: {e}")
            return {"domain": "通用", "omissions": []}
    




# ==================== 演示场景 ====================
def demo_content_improvement():
    """演示内容改进流程"""
    print("\n📝 === 内容改进演示 ===")
    
    system = ReflectionSystem()
    
    # 测试任务定义 - 仅在这里定义，不绑定到通用实现
    task = """设计一个结合三国杀和狼人杀规则的桌游，要求：
- 800字左右的设计方案
- 包含游戏背景设定和角色设计
- 详细说明游戏规则和流程
- 分析游戏平衡性和可玩性
- 提供具体的游戏配件清单
- 考虑不同玩家数量的适配性"""
    
    try:
        result = system.generate_with_reflection(task)
        
        print("\n📊 === 改进效果对比 ===")
        print(f"原始内容长度: {len(result['original_content'])} 字符")
        print(f"改进内容长度: {len(result['improved_content'])} 字符")
        print(f"是否进行了改进: {'是' if result['improvement_applied'] else '否'}")
        
        if result["reflection"].get("omissions"):
            print(f"发现的遗漏点数量: {len(result['reflection']['omissions'])}")
            for i, omission in enumerate(result["reflection"]["omissions"], 1):
                print(f"  {i}. {omission.get('description', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 演示出现错误: {e}")
        return None



# ==================== 主程序 ====================
def main():
    """主演示程序"""
    print("🧠 === AutoGen 反思改进系统演示 ===")
    print("展示基于反思的内容质量持续优化机制")
    print("="*60)
    
    # 环境检查
    try:
        llm_config = get_llm_config()
        print("✅ LLM 配置检查通过")
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    print(f"\n📚 当前反思记忆: {len(memory.entries)} 条历史记录")
    
    try:
        # 完整流程演示
        demo_content_improvement()
        
        print("\n" + "="*60)
        print("🎉 === 反思改进系统演示完成 ===")
        
        print("\n📊 === 系统能力总结 ===")
        print("✅ **遗漏识别**: 系统性发现内容中的遗漏点和不足")
        print("✅ **质量改进**: 基于反思结果迭代优化内容质量")
        print("✅ **经验积累**: 历史反思经验指导未来内容生成")
        print("✅ **多智能体协作**: 专业分工提高分析和改进质量")
        print("✅ **持续学习**: 反思系统不断学习和完善")
        print("✅ **语义检索**: 基于嵌入向量的智能记忆检索")
        
        print("\n💡 === 关键价值 ===")
        print("• 系统性提升内容创作质量")
        print("• 建立组织级的内容改进知识库") 
        print("• 实现内容创作的持续优化")
        print("• 降低内容遗漏和质量风险")
        print("• 培养反思性思维和质量意识")
        
        print(f"\n📁 反思记忆保存在: {memory.memory_file}")
        print(f"📈 总计积累反思经验: {len(memory.entries)} 条")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
