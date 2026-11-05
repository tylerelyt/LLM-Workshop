# -*- coding: utf-8 -*-
"""
Context Engineering Prompt Builder - 基于上下文工程的Prompt构建器

本模块实现了一个先进的Prompt构建系统，将Prompt划分为四个核心分区：
1. 人设记忆 (Persona Memory) - AI的身份和行为特征
2. 工具分区 (Tools Partition) - 可用工具的定义和使用说明
3. 情节记忆 (Episodic Memory) - 从MemGPT获取的对话上下文
4. 语义记忆 (Semantic Memory) - 从RAG系统检索的知识内容
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any, Optional, Union
from datetime import datetime
from enum import Enum


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型枚举"""
    PERSONA = "persona"
    TOOLS = "tools" 
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


@dataclass
class ConversationTurn:
    """对话轮次数据结构"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryPartition:
    """记忆分区数据结构"""
    type: MemoryType
    content: str
    priority: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryProvider(ABC):
    """记忆提供者抽象基类"""
    
    @abstractmethod
    def retrieve_memory(self, query: str, context: Dict[str, Any]) -> str:
        """检索记忆内容"""
        pass
    
    @abstractmethod
    def update_memory(self, content: str, metadata: Dict[str, Any]) -> bool:
        """更新记忆内容"""
        pass


class MemGPTProvider(MemoryProvider):
    """MemGPT情节记忆提供者"""
    
    def __init__(self, api_endpoint: Optional[str] = None, max_context_length: int = 4000):
        self.api_endpoint = api_endpoint or "http://localhost:8283"
        self.max_context_length = max_context_length
        self.memory_cache = {}
    
    def retrieve_memory(self, query: str, context: Dict[str, Any]) -> str:
        """从MemGPT获取情节记忆"""
        try:
            logger.info(f"[MemGPT] 正在检索情节记忆，查询: {query[:50]}...")
            
            # 获取对话历史
            conversation_history = context.get('conversation_history', [])
            
            if not conversation_history:
                return "这是对话的开始，暂无历史记忆。"
            
            # 智能摘要生成
            summary = self._generate_intelligent_summary(conversation_history, query)
            
            # 提取关键上下文
            key_contexts = self._extract_key_contexts(conversation_history, query)
            
            # 构建情节记忆
            episodic_memory = f"""
## 对话摘要
{summary}

## 关键上下文
{key_contexts}

## 情感状态
{self._analyze_conversation_mood(conversation_history)}
"""
            
            logger.info("[MemGPT] 情节记忆检索完成")
            return episodic_memory.strip()
            
        except Exception as e:
            logger.error(f"MemGPT记忆检索失败: {e}")
            return "情节记忆暂时不可用，将基于当前对话继续。"
    
    def _generate_intelligent_summary(self, conversation_history: List[ConversationTurn], current_query: str) -> str:
        """生成智能对话摘要"""
        if len(conversation_history) <= 3:
            return "对话刚开始，用户正在探索和了解系统能力。"
        
        # 分析对话主题
        topics = self._extract_topics(conversation_history)
        user_intent = self._analyze_user_intent(conversation_history, current_query)
        
        return f"用户主要关注: {', '.join(topics)}。当前意图: {user_intent}"
    
    def _extract_key_contexts(self, conversation_history: List[ConversationTurn], query: str) -> str:
        """提取关键上下文信息"""
        key_points = []
        
        # 获取最近的重要对话
        recent_turns = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        for turn in recent_turns:
            if len(turn.content) > 20:  # 过滤掉太短的回复
                role_name = "用户" if turn.role == "user" else "助手"
                key_points.append(f"- {role_name}: {turn.content[:100]}...")
        
        return "\n".join(key_points) if key_points else "暂无关键上下文。"
    
    def _extract_topics(self, conversation_history: List[ConversationTurn]) -> List[str]:
        """提取对话主题"""
        # 简化的主题提取（实际应用中可使用NLP技术）
        topics = set()
        keywords = ["RAG", "MemGPT", "AI", "机器学习", "深度学习", "自然语言处理", "提示工程"]
        
        for turn in conversation_history:
            for keyword in keywords:
                if keyword.lower() in turn.content.lower():
                    topics.add(keyword)
        
        return list(topics) if topics else ["一般对话"]
    
    def _analyze_user_intent(self, conversation_history: List[ConversationTurn], current_query: str) -> str:
        """分析用户意图"""
        if "什么是" in current_query or "解释" in current_query:
            return "寻求知识解释"
        elif "如何" in current_query or "怎么" in current_query:
            return "寻求操作指导"
        elif "比较" in current_query or "区别" in current_query:
            return "寻求比较分析"
        else:
            return "一般询问"
    
    def _analyze_conversation_mood(self, conversation_history: List[ConversationTurn]) -> str:
        """分析对话情感状态"""
        if not conversation_history:
            return "中性"
        
        # 简化的情感分析
        last_user_turn = None
        for turn in reversed(conversation_history):
            if turn.role == "user":
                last_user_turn = turn
                break
        
        if last_user_turn:
            content = last_user_turn.content.lower()
            if any(word in content for word in ["谢谢", "很好", "棒", "喜欢"]):
                return "积极"
            elif any(word in content for word in ["不", "错", "问题", "困惑"]):
                return "困惑"
        
        return "中性"
    
    def update_memory(self, content: str, metadata: Dict[str, Any]) -> bool:
        """更新情节记忆"""
        try:
            # 在实际应用中，这里会调用MemGPT API
            logger.info("[MemGPT] 情节记忆已更新")
            return True
        except Exception as e:
            logger.error(f"MemGPT记忆更新失败: {e}")
            return False


class RAGProvider(MemoryProvider):
    """RAG语义记忆提供者"""
    
    def __init__(self, knowledge_base_path: Optional[str] = None, embedding_model: str = "default"):
        self.knowledge_base_path = knowledge_base_path
        self.embedding_model = embedding_model
        self.knowledge_cache = {}
        self._init_knowledge_base()
    
    def _init_knowledge_base(self):
        """初始化知识库"""
        self.knowledge_base = {
            "RAG": {
                "definition": "检索增强生成（Retrieval-Augmented Generation）是一种AI技术，它将预训练语言模型的生成能力与外部知识库的检索能力相结合。",
                "components": ["检索器", "生成器", "知识库"],
                "advantages": ["提高准确性", "减少幻觉", "支持实时信息"],
                "use_cases": ["问答系统", "内容生成", "知识管理"]
            },
            "MemGPT": {
                "definition": "MemGPT是一种为大型语言模型提供长期记忆能力的系统，通过分层记忆架构实现持久化对话上下文。",
                "features": ["长期记忆", "上下文管理", "自主记忆操作"],
                "architecture": ["核心记忆", "归档记忆", "递归摘要"],
                "benefits": ["对话连贯性", "个性化体验", "知识积累"]
            },
            "Context Engineering": {
                "definition": "上下文工程是设计和优化大语言模型输入提示的技术和方法论。",
                "principles": ["明确性", "结构性", "相关性", "简洁性"],
                "techniques": ["分区设计", "示例学习", "角色设定", "任务分解"],
                "best_practices": ["使用清晰分隔符", "提供具体示例", "明确期望输出格式"]
            },
            "Prompt Engineering": {
                "definition": "提示工程是设计有效提示来引导AI模型产生期望输出的艺术和科学。",
                "strategies": ["零样本学习", "少样本学习", "思维链", "角色扮演"],
                "optimization": ["迭代改进", "A/B测试", "效果评估", "模板化"],
                "challenges": ["模型差异", "任务复杂度", "输出一致性", "成本控制"]
            }
        }
    
    def retrieve_memory(self, query: str, context: Dict[str, Any]) -> str:
        """从RAG系统检索语义记忆"""
        try:
            logger.info(f"[RAG] 正在检索语义记忆，查询: {query[:50]}...")
            
            # 计算查询相关性
            relevant_docs = self._semantic_search(query)
            
            # 构建语义记忆
            if relevant_docs:
                semantic_memory = self._format_retrieved_knowledge(relevant_docs, query)
            else:
                semantic_memory = self._generate_fallback_response(query)
            
            logger.info("[RAG] 语义记忆检索完成")
            return semantic_memory
            
        except Exception as e:
            logger.error(f"RAG记忆检索失败: {e}")
            return "语义记忆暂时不可用，将基于已有知识回答。"
    
    def _semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """执行语义搜索"""
        query_lower = query.lower()
        relevant_docs = []
        
        # 关键词匹配和相关性评分
        for topic, content in self.knowledge_base.items():
            relevance_score = self._calculate_relevance(query_lower, topic, content)
            if relevance_score > 0.3:  # 相关性阈值
                relevant_docs.append({
                    "topic": topic,
                    "content": content,
                    "relevance": relevance_score
                })
        
        # 按相关性排序
        relevant_docs.sort(key=lambda x: x["relevance"], reverse=True)
        return relevant_docs[:3]  # 返回最相关的3个文档
    
    def _calculate_relevance(self, query: str, topic: str, content: Dict) -> float:
        """计算查询与文档的相关性"""
        score = 0.0
        
        # 主题匹配
        if topic.lower() in query:
            score += 1.0
        
        # 内容匹配
        all_text = " ".join([str(v) for v in content.values()]).lower()
        query_words = query.split()
        
        for word in query_words:
            if word in all_text:
                score += 0.2
        
        return min(score, 1.0)  # 限制最大分数为1.0
    
    def _format_retrieved_knowledge(self, docs: List[Dict], query: str) -> str:
        """格式化检索到的知识"""
        formatted_content = []
        
        for doc in docs:
            topic = doc["topic"]
            content = doc["content"]
            
            formatted_content.append(f"""
### {topic}
**定义**: {content.get('definition', 'N/A')}
**关键特征**: {', '.join(content.get('features', content.get('components', content.get('principles', []))))}
**相关性**: {doc['relevance']:.2f}
""")
        
        return "\n".join(formatted_content).strip()
    
    def _generate_fallback_response(self, query: str) -> str:
        """生成后备响应"""
        return f"""
暂未在知识库中找到与"{query}"直接相关的信息。
建议：
1. 尝试使用更具体的关键词
2. 检查拼写是否正确
3. 考虑使用同义词进行搜索
"""
    
    def update_memory(self, content: str, metadata: Dict[str, Any]) -> bool:
        """更新语义知识库"""
        try:
            # 在实际应用中，这里会更新向量数据库
            logger.info("[RAG] 知识库已更新")
            return True
        except Exception as e:
            logger.error(f"RAG知识库更新失败: {e}")
            return False


class AdvancedContextPromptBuilder:
    """高级上下文工程Prompt构建器"""
    
    def __init__(self, 
                 persona_profile: str,
                 tools_definition: str,
                 memgpt_provider: Optional[MemGPTProvider] = None,
                 rag_provider: Optional[RAGProvider] = None):
        """
        初始化高级Prompt构建器
        
        Args:
            persona_profile: AI人设描述
            tools_definition: 工具定义
            memgpt_provider: MemGPT记忆提供者
            rag_provider: RAG记忆提供者
        """
        self.persona = persona_profile
        self.tools = tools_definition
        self.memgpt_provider = memgpt_provider or MemGPTProvider()
        self.rag_provider = rag_provider or RAGProvider()
        
        # 性能监控
        self.performance_metrics = {
            "total_prompts": 0,
            "avg_build_time": 0,
            "memory_retrieval_times": []
        }
        
        logger.info("高级上下文工程Prompt构建器初始化完成")
    
    def construct_optimized_prompt(self, 
                                 user_query: str, 
                                 conversation_history: List[Dict[str, str]],
                                 priority_weights: Optional[Dict[str, float]] = None) -> str:
        """
        构建优化的结构化Prompt
        
        Args:
            user_query: 用户查询
            conversation_history: 对话历史
            priority_weights: 各分区优先级权重
            
        Returns:
            完整的结构化Prompt
        """
        start_time = time.time()
        
        try:
            # 转换对话历史格式
            converted_history = self._convert_conversation_history(conversation_history)
            
            # 设置默认权重
            weights = priority_weights or {
                "persona": 1.0,
                "tools": 0.8,
                "episodic": 0.9,
                "semantic": 1.0
            }
            
            # 并行获取记忆内容
            memory_partitions = self._retrieve_all_memories(user_query, converted_history, weights)
            
            # 构建分区化Prompt
            structured_prompt = self._build_structured_prompt(user_query, memory_partitions)
            
            # 更新性能指标
            self._update_performance_metrics(time.time() - start_time)
            
            logger.info("优化Prompt构建完成")
            return structured_prompt
            
        except Exception as e:
            logger.error(f"Prompt构建失败: {e}")
            return self._build_fallback_prompt(user_query)
    
    def _convert_conversation_history(self, history: List[Dict[str, str]]) -> List[ConversationTurn]:
        """转换对话历史格式"""
        converted = []
        for turn in history:
            converted.append(ConversationTurn(
                role=turn.get('role', 'user'),
                content=turn.get('content', ''),
                metadata=turn.get('metadata', {})
            ))
        return converted
    
    def _retrieve_all_memories(self, 
                             query: str, 
                             history: List[ConversationTurn],
                             weights: Dict[str, float]) -> List[MemoryPartition]:
        """并行检索所有记忆分区"""
        partitions = []
        
        # 构建上下文
        context = {
            'conversation_history': history,
            'query': query,
            'timestamp': datetime.now()
        }
        
        # 获取情节记忆
        if weights.get("episodic", 0) > 0:
            episodic_content = self.memgpt_provider.retrieve_memory(query, context)
            partitions.append(MemoryPartition(
                type=MemoryType.EPISODIC,
                content=episodic_content,
                priority=int(weights.get("episodic", 1) * 10)
            ))
        
        # 获取语义记忆
        if weights.get("semantic", 0) > 0:
            semantic_content = self.rag_provider.retrieve_memory(query, context)
            partitions.append(MemoryPartition(
                type=MemoryType.SEMANTIC,
                content=semantic_content,
                priority=int(weights.get("semantic", 1) * 10)
            ))
        
        # 添加固定分区
        partitions.extend([
            MemoryPartition(
                type=MemoryType.PERSONA,
                content=self.persona,
                priority=int(weights.get("persona", 1) * 10)
            ),
            MemoryPartition(
                type=MemoryType.TOOLS,
                content=self.tools,
                priority=int(weights.get("tools", 1) * 10)
            )
        ])
        
        # 按优先级排序
        partitions.sort(key=lambda x: x.priority, reverse=True)
        return partitions
    
    def _build_structured_prompt(self, query: str, partitions: List[MemoryPartition]) -> str:
        """构建结构化Prompt"""
        
        prompt_sections = []
        
        # 添加Prompt头部
        prompt_sections.append("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          CONTEXT-ENGINEERED PROMPT SYSTEM                     ║
║                             基于上下文工程的智能Prompt系统                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # 按类型组织分区
        for partition in partitions:
            section_title = self._get_section_title(partition.type)
            section_content = self._format_section_content(partition)
            
            prompt_sections.append(f"""
┌─ {section_title} ─┐
{section_content}
└─ END {partition.type.value.upper()} ─┘
""")
        
        # 添加用户查询部分
        prompt_sections.append(f"""
┌─ 用户查询 (USER QUERY) ─┐
{query}
└─ END USER QUERY ─┘

请基于以上上下文信息，为用户提供准确、有帮助的回答。
""")
        
        return "\n".join(prompt_sections)
    
    def _get_section_title(self, memory_type: MemoryType) -> str:
        """获取分区标题"""
        titles = {
            MemoryType.PERSONA: "人设记忆 (PERSONA MEMORY)",
            MemoryType.TOOLS: "可用工具 (AVAILABLE TOOLS)", 
            MemoryType.EPISODIC: "情节记忆 (EPISODIC MEMORY)",
            MemoryType.SEMANTIC: "语义记忆 (SEMANTIC MEMORY)"
        }
        return titles.get(memory_type, "未知分区")
    
    def _format_section_content(self, partition: MemoryPartition) -> str:
        """格式化分区内容"""
        content = partition.content.strip()
        
        # 添加时间戳和优先级信息
        metadata_info = f"[优先级: {partition.priority}/10] [时间: {partition.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]"
        
        return f"{metadata_info}\n\n{content}"
    
    def _build_fallback_prompt(self, query: str) -> str:
        """构建后备Prompt"""
        return f"""
系统出现异常，使用简化模式：

人设: {self.persona}

工具: {self.tools}

用户查询: {query}

请尽力回答用户的问题。
"""
    
    def _update_performance_metrics(self, build_time: float):
        """更新性能指标"""
        self.performance_metrics["total_prompts"] += 1
        self.performance_metrics["memory_retrieval_times"].append(build_time)
        
        # 计算平均构建时间
        total_time = sum(self.performance_metrics["memory_retrieval_times"])
        self.performance_metrics["avg_build_time"] = total_time / len(self.performance_metrics["memory_retrieval_times"])
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "total_prompts_built": self.performance_metrics["total_prompts"],
            "average_build_time_seconds": round(self.performance_metrics["avg_build_time"], 4),
            "last_10_build_times": self.performance_metrics["memory_retrieval_times"][-10:],
            "system_status": "正常运行" if self.performance_metrics["avg_build_time"] < 2.0 else "性能警告"
        }


# === 使用示例和测试代码 ===
def create_demo_scenario():
    """创建演示场景"""
    
    # 1. 定义增强的人设
    enhanced_persona = """
你是"智心"（ZhiXin），一个专业的AI技术顾问和研究助手。

## 核心特征
- 深度专业: 在AI、机器学习、自然语言处理领域拥有深厚知识
- 善于教学: 能将复杂概念用简单易懂的方式解释
- 实用导向: 不仅提供理论知识，还能给出实际应用建议
- 持续学习: 乐于探索新技术和前沿研究

## 交互风格
- 回答准确且有据可查
- 结构清晰，层次分明
- 适时提供代码示例和实践建议
- 鼓励用户深入思考和探索

## 专业领域
- 大语言模型架构与优化
- 提示工程与上下文设计
- RAG系统构建与优化
- 记忆增强AI系统（如MemGPT）
- 多模态AI应用开发
"""
    
    # 2. 定义增强的工具集
    enhanced_tools = """
## 可用工具集

### 计算工具
<tool>
  <name>advanced_calculator</name>
  <description>执行复杂数学计算，支持统计分析和数据处理</description>
  <parameters>
    {
      "expression": "数学表达式或统计函数",
      "format": "输出格式 (decimal/scientific/percentage)"
    }
  </parameters>
  <examples>["calculate_accuracy(tp=85, fp=10, fn=5)", "mean([1,2,3,4,5])"]</examples>
</tool>

### 搜索工具
<tool>
  <name>web_search</name>
  <description>搜索最新的技术资讯和研究论文</description>
  <parameters>
    {
      "query": "搜索关键词",
      "source": "搜索来源 (arxiv/github/general)",
      "date_range": "时间范围 (recent/year/all)"
    }
  </parameters>
</tool>

### 代码工具
<tool>
  <name>code_analyzer</name>
  <description>分析和优化代码，提供改进建议</description>
  <parameters>
    {
      "code": "要分析的代码",
      "language": "编程语言",
      "analysis_type": "分析类型 (performance/security/style)"
    }
  </parameters>
</tool>

### 知识图谱工具
<tool>
  <name>knowledge_graph_query</name>
  <description>查询知识图谱中的实体关系和概念连接</description>
  <parameters>
    {
      "entity": "查询实体",
      "relation_type": "关系类型",
      "depth": "查询深度"
    }
  </parameters>
</tool>
"""
    
    # 3. 初始化提供者
    memgpt_provider = MemGPTProvider(api_endpoint="http://localhost:8283")
    rag_provider = RAGProvider()
    
    # 4. 创建高级构建器
    prompt_builder = AdvancedContextPromptBuilder(
        persona_profile=enhanced_persona,
        tools_definition=enhanced_tools,
        memgpt_provider=memgpt_provider,
        rag_provider=rag_provider
    )
    
    return prompt_builder


def run_comprehensive_demo():
    """运行综合演示"""
    print("\n" + "="*80)
    print("              高级上下文工程Prompt构建器 - 综合演示")
    print("="*80)
    
    # 创建演示环境
    builder = create_demo_scenario()
    
    # 模拟复杂对话历史
    complex_conversation = [
        {'role': 'user', 'content': '你好，我想了解一些关于现代AI技术的知识。'},
        {'role': 'assistant', 'content': '你好！我是智心，很高兴为你介绍AI技术。你对哪个方面特别感兴趣？'},
        {'role': 'user', 'content': '我听说过RAG技术，但不太明白它的工作原理。'},
        {'role': 'assistant', 'content': 'RAG（检索增强生成）是一项重要技术...[详细解释]'},
        {'role': 'user', 'content': '那MemGPT和RAG有什么关系吗？它们能结合使用吗？'},
        {'role': 'assistant', 'content': 'MemGPT和RAG确实可以很好地结合...[详细说明]'},
    ]
    
    # 当前复杂查询
    current_query = """
    我想深入了解如何在实际项目中将MemGPT的记忆管理能力与RAG的知识检索能力结合起来。
    具体来说：
    1. 它们在架构上如何协同工作？
    2. 有哪些技术挑战需要解决？
    3. 能否提供一些实现建议和最佳实践？
    """
    
    # 自定义权重
    priority_weights = {
        "persona": 0.9,
        "tools": 0.7,
        "episodic": 1.0,  # 对话上下文很重要
        "semantic": 1.0   # 技术知识很重要
    }
    
    print("\n📝 构建中...")
    
    # 构建高级Prompt
    advanced_prompt = builder.construct_optimized_prompt(
        user_query=current_query,
        conversation_history=complex_conversation,
        priority_weights=priority_weights
    )
    
    print("\n✨ 构建完成！")
    print("\n" + "─"*80)
    print("生成的高级结构化Prompt:")
    print("─"*80)
    print(advanced_prompt)
    
    # 显示性能报告
    print("\n" + "─"*80)
    print("性能报告:")
    print("─"*80)
    performance = builder.get_performance_report()
    for key, value in performance.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    try:
        run_comprehensive_demo()
    except KeyboardInterrupt:
        print("\n\n演示被用户中断。")
    except Exception as e:
        logger.error(f"演示运行出错: {e}")
        print(f"\n演示出现错误: {e}")