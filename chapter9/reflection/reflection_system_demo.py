#!/usr/bin/env python3
"""
反思与改进系统演示

展示如何构建基于反思的内容改进系统，通过多智能体协作实现：
1. 内容生成和质量分析
2. 系统性发现遗漏点
3. 基于反思的内容改进
4. 长期记忆和经验积累

基于 AutoGen 的真实实现，支持语义检索的遗漏点记忆系统。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import load_environment


import argparse
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from autogen import AssistantAgent

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
        local_name = os.getenv("WORKSHOP_LOCAL_EMBEDDING_MODEL")
        self._local_embedding = None
        if local_name:
            from fastembed import TextEmbedding

            self._local_embedding = TextEmbedding(local_name)
        self._embedding_client = None if local_name else self._init_embedding_client()
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
        if self._local_embedding is not None:
            return next(iter(self._local_embedding.embed([text])))
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
            raise RuntimeError("记忆文件非空，但本轮未取得嵌入向量；请配置本地嵌入或 DashScope 后再验证召回。")

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
        Path(self.memory_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)

    def load_memory(self) -> None:
        if not os.path.exists(self.memory_file):
            return
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 新版仅支持扁平列表
            if not isinstance(data, list):
                raise ValueError("记忆文件应为条目数组；请使用新的记忆路径，保留旧文件。")
            self.entries = data
        except json.JSONDecodeError as error:
            raise ValueError("记忆文件不是有效 JSON；请检查文件或使用新的记忆路径。") from error

# 全局记忆系统实例
memory = None  # 在运行入口初始化，导入模块不会下载模型或读取默认记忆。

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

# ==================== 反思改进流程 ====================
class ReflectionSystem:
    """反思改进系统 - 基于标准反思学习架构"""
    
    def __init__(self):
        global memory
        if memory is None:
            memory = OmissionMemory(os.getenv("WORKSHOP_REFLECTION_MEMORY"))
        # 按照反思学习架构创建智能体
        self.actor = create_actor()           # Actor: 负责内容生成和行动执行
        self.evaluator = create_evaluator()   # Evaluator: 负责评估内容质量
        self.self_reflection = create_self_reflection()  # Self-reflection: 负责深度反思
    
    def generate_with_reflection(self, task: str, *, baseline: str | None = None) -> Dict:
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
        
        generated_content = baseline if baseline is not None else self._ask(self.actor, generation_prompt)
        print("✅ 初始内容已取得")
        
        # 第三步：Evaluator评估内容质量
        print("\n📊 步骤3: Evaluator评估内容质量...")
        evaluation_prompt = f"""请评估以下内容的质量：

任务：{task}

内容：
{generated_content}

请从完整性、逻辑性、实用性、前瞻性、受众适配等维度进行全面评估。"""
        
        evaluation_result = self._ask(self.evaluator, evaluation_prompt)
        
        # 第四步：Self-reflection深度反思
        print("\n🧠 步骤4: Self-reflection深度反思...")
        reflection_prompt = f"""基于评估结果，请进行深度反思：

原始任务：
{task}

原始内容：
{generated_content}

评估结果：
{evaluation_result}

请深入分析内容中的问题和不足，提取经验教训，并提供具体的改进建议。"""
        
        reflection_result = self._parse_reflection(self._ask(self.self_reflection, reflection_prompt))
        
        # 第五步：基于反思结果改进内容
        if reflection_result.get("omissions"):
            print(f"\n🔄 步骤5: 基于反思结果改进内容 (发现 {len(reflection_result['omissions'])} 个改进点)...")
            
            improvement_prompt = f"""基于反思结果，请重新优化内容：

原始任务：
{task}

原始内容：
{generated_content}

反思结果：
{json.dumps(reflection_result, ensure_ascii=False, indent=2)}

{experience_context}

请生成改进后的完整内容，确保解决反思中发现的遗漏点。"""
            
            improved_content = self._ask(self.actor, improvement_prompt)
        else:
            print("模型未报告遗漏，本轮沿用原稿；请人工核对。")
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
            "retrieved_memories": historical_experience,
            "memory_context_in_revision": experience_context,
            "original_content": generated_content,
            "improved_content": improved_content,
            "evaluation": evaluation_result,
            "reflection": reflection_result,
            "improvement_applied": len(reflection_result.get("omissions", [])) > 0
        }
        
        print("\n🎉 反思改进流程完成！")
        return result
    
    def _ask(self, agent, prompt: str) -> str:
        ok, answer = agent.generate_oai_reply(messages=[{"role": "user", "content": prompt}])
        if isinstance(answer, dict):
            answer = answer.get("content")
        if not ok:
            raise RuntimeError(f"{agent.name} 未完成模型调用。")
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(f"{agent.name} 没有返回可用内容。")
        return answer.strip()

    def _parse_reflection(self, content: str) -> Dict:
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        try:
            result = json.loads(fenced.group(1) if fenced else content)
        except json.JSONDecodeError:
            raise RuntimeError("反思模型没有返回可解析的 JSON。") from None
        if not isinstance(result, dict) or not isinstance(result.get("omissions"), list):
            raise RuntimeError("反思结果缺少 omissions 列表。")
        return result



def show_content_comparison(result):
    """把本轮草稿、模型诊断与实际改稿放在一起供人工核对。"""
    import difflib
    import textwrap
    def excerpt(text, limit=500):
        return text if len(text) <= limit else text[:limit] + "\n…内容较长，使用 --output 保存完整内容。"
    print("\n=== 草稿 → 反思 → 实际改稿 ===")
    print("原稿：\n" + excerpt(result["original_content"]))
    print("模型评估（不是独立验收）：\n" + excerpt(result["evaluation"]))
    omissions = result["reflection"].get("omissions", [])
    for i, omission in enumerate(omissions, 1):
        print(f"遗漏 {i}：{omission.get('description', '')}；建议：{omission.get('suggestion', '')}")
    def lines(content):
        return [line for paragraph in content.splitlines() for line in (textwrap.wrap(paragraph, 44) or [""])]
    changes = list(difflib.unified_diff(lines(result["original_content"]), lines(result["improved_content"]),
                                      fromfile="草稿", tofile="改稿", lineterm="", n=1))
    print("实际文字差异（最多 36 行）：")
    print("\n".join(changes[:36]) if changes else "内容没有变化。")
    if len(changes) > 36:
        print("…差异较长，可用 --output 保存完整改稿。")
    if not omissions:
        print("本轮没有识别出遗漏，请人工核对是否漏评。")
    for entry in result["retrieved_memories"]:
        print(f"本轮召回经验：{entry.get('description', '')}；建议：{entry.get('suggestion', '')}")


def demo_content_improvement(baseline_file=None):
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
    
    baseline = Path(baseline_file).read_text() if baseline_file else None
    if baseline is None and not memory.entries:
        # A fixed incomplete draft makes the first observation reproducible.
        baseline = "设计一款八人桌游：玩家暗选忠臣或反贼，通过日间投票与夜间行动争夺胜利。"
        print(f"首轮教学草稿（故意省略规则细节和配件清单）：{baseline}")
    try:
        result = system.generate_with_reflection(task, baseline=baseline)
        if baseline is not None and not result["improvement_applied"]:
            raise RuntimeError("反思未找出教学草稿中预留的遗漏，请检查评估输出。")
        
        show_content_comparison(result)

        return result
        
    except Exception as e:
        print(f"❌ 演示出现错误: {e}")
        return None



# ==================== 主程序 ====================
def main():
    """主演示程序"""
    global memory
    parser = argparse.ArgumentParser(description="检查草稿遗漏、保存反思并在新进程中召回")
    parser.add_argument("--memory-file", default=os.getenv("WORKSHOP_REFLECTION_MEMORY"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline-file", type=Path)
    args = parser.parse_args()

    print("🧠 === AutoGen 反思改进系统演示 ===")
    print("展示基于反思的内容质量持续优化机制")
    print("="*60)
    
    # 环境检查
    try:
        llm_config = get_llm_config()
        print("✅ LLM 配置检查通过")
    except ValueError as e:
        raise SystemExit(f"❌ {e}") from None
    
    memory = OmissionMemory(args.memory_file)
    print(f"\n📚 当前反思记忆: {len(memory.entries)} 条历史记录")
    
    try:
        # 完整流程演示
        result = demo_content_improvement(args.baseline_file)
        if result is None:
            raise SystemExit(1)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n" + "="*60)
        print("🎉 === 反思改进系统演示完成 ===")
        
        print("请核对改稿是否解决上述遗漏；模型评审和内容差异不等于独立质量判定。")
        if args.output:
            print(f"完整内容与评审：{args.output}")

        print(f"\n📁 反思记忆保存在: {memory.memory_file}")
        print(f"📈 总计积累反思经验: {len(memory.entries)} 条")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()
