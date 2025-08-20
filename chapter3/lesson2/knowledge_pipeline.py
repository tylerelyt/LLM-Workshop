#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Knowledge Graph Construction from Text with Chain-of-Thought

This script demonstrates an advanced, robust pipeline for building a knowledge graph
from unstructured text using Large Language Models with Chain-of-Thought reasoning.

Pipeline Steps:
1.  **Candidate Extraction**: Extract entities, relations, and attributes from text
2.  **Schema Optimization**: Refine and normalize entity/relation/attribute types
3.  **Refinement & Relabeling**: Apply the optimized schema to candidates
4.  **Role Analysis**: Perform Chain-of-Thought analysis to identify unique entities
5.  **Context-Aware Entity Linking**: Use role analysis for accurate entity linking

Dependencies: pip install openai networkx pyvis
Setup: Set your LLM API key as environment variable (e.g., DASHSCOPE_API_KEY).
"""

from __future__ import annotations
import json
import os
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
from pyvis.network import Network
# =============================================================================
# --- PROMPT TEMPLATES SECTION  (with one‑shot demonstrations) ---
# =============================================================================

FREE_EXTRACTION_PROMPT = """-任务目标-
你是一个信息抽取专家。请根据给定文本构建知识图谱，识别所有重要的实体和它们之间的关系。

-核心构建原则-
1.  **明确区分三种概念类型**：
   - **实体(Entity)**: 独立存在的对象、人物、地点、概念等（如：张三、公司、北京）
   - **关系(Relation)**: 实体之间的动作、交互或联系（如：工作于、位于、管理）
   - **属性(Attribute)**: 实体的特征、状态或性质（如：年龄、颜色、情感状态）
2.  **实体识别原则**：识别具有独立性的核心对象，包括专有名称、产品型号、组织机构等。
3.  **关系识别原则**：重点关注实体间的动作词、介词短语和动态联系，确保关系方向正确。
4.  **属性处理原则**：将形容词、状态词、特征词作为实体的属性，而非独立实体。
5.  **完整性原则**：确保抽取文本中提到的所有重要实体和关系，包括技术规格、数量信息等。
6.  **优先使用最具体的名称**（如专有名称）作为关系的主语和宾语。
7.  **保持关系的具体语义**：使用原文中的具体动作词，不要过度概括。
8.  识别并统一指向同一对象的不同表述（共指消解）。

-输出格式-
请严格返回以下JSON格式的对象：
{{
  "entities": [
    {{"name": "实体名称", "type": "实体类型", "description": "简要描述", "attributes": {{"属性名": "属性值"}}}}
  ],
  "relations": [
    {{"subject": "主语实体", "predicate": "关系", "object": "宾语实体"}}
  ]
}}

-示例演示-
输入文本（《企业组织架构说明》节选）：
  "资深工程师李明负责技术团队，他性格开朗且经验丰富。李明直接向CTO王总汇报工作进展。"

期望输出：
{{
  "entities": [
    {{"name":"李明","type":"Person","description":"资深工程师", "attributes": {{"职位": "资深工程师", "性格": "开朗", "经验": "丰富"}}}},
    {{"name":"技术团队","type":"Organization","description":"技术开发团队", "attributes": {{}}}},
    {{"name":"王总","type":"Person","description":"CTO", "attributes": {{"职位": "CTO"}}}}
  ],
  "relations":[
    {{"subject":"李明","predicate":"负责","object":"技术团队"}},
    {{"subject":"李明","predicate":"汇报","object":"王总"}}
  ]
}}
"""

# ---------------------------------------------------------------------------

SCHEMA_OPTIMIZATION_PROMPT = """-任务目标-
你是一个数据架构师。请基于以下从文本中抽取的知识，优化其Schema（实体类型、关系类型和属性类型），使其更加规范和一致。

-原始图谱信息-
实体列表（示例）:
{entities}
关系列表（示例）:
{relations}

-优化原则-
- 合并相似的类型，但不要过度泛化。
- **保持关系的具体语义**：意义明确不同的关系类型应保持独立（如"管理"和"协作"、"创建"和"删除"等）。
- **属性类型规范化**：将实体的特征、状态、性质归类为标准属性类型。
- 使用业界通用的、简洁明确的命名。
- **优先保留语义丰富的原始关系词**，除非确实需要规范化。

-输出格式-
请返回一个包含优化后类型列表的JSON对象：
{{
  "entities": ["优化后的实体类型1", ...],
  "relations": ["优化后的关系类型1", ...],
  "attributes": ["优化后的属性类型1", ...]
}}

-示例演示-
输入（节选）：
  实体类型: ["Person","员工","Manager","系统","Module"]
  关系类型: ["管理","supervise","负责","创建","生成"]
  属性类型: ["年龄","姓名","状态","级别","经验"]

示例输出：
{{
  "entities": ["Person","System"],
  "relations": ["管理","创建"],
  "attributes": ["基本信息","状态","级别"]
}}
"""

# ---------------------------------------------------------------------------

REFINE_AND_RELABEL_PROMPT = """-任务目标-
你是一个知识工程师。你的任务是根据一个"优化后的标准Schema"，对一份"候选三元组列表"进行精炼、重标记和过滤。

-优化后的标准Schema-
这是唯一允许使用的类型定义：
{schema}

-候选三元组列表-
这是需要被处理的数据：
{triples}

-处理指令-
1.  遍历每一条候选三元组。
2.  对于三元组中的谓词(predicate)，将其重命名为新Schema中最匹配的关系类型。
3.  **优先保留关系**：尽量将原始关系映射到Schema中语义最接近的关系类型，只有在完全无法映射时才丢弃。

-输出格式-
请返回一个只包含精炼后三元组列表的JSON对象：
{{
  "refined_triples": [
    {{"subject": "主语实体", "predicate": "符合新Schema的关系", "object": "宾语实体"}}
  ]
}}

-示例演示-
标准Schema（示例）：
  实体类型: ["Actor","Module"]
  关系类型: ["创建","触发"]

候选三元组：
  [
    {{"subject":"系统","predicate":"generate","object":"日志模块"}},
    {{"subject":"用户","predicate":"produce","object":"请求"}}
  ]

示例输出：
{{
  "refined_triples": [
    {{"subject":"系统","predicate":"创建","object":"日志模块"}}
  ]
}}
"""

# ---------------------------------------------------------------------------

ROLE_ANALYSIS_PROMPT = """-任务目标-
你是一位逻辑缜密的文档分析专家。你的任务是仔细阅读以下文本，并确定文档中每种“角色类型”（如系统管理员、访客）各有多少个独立的个体。

-待分析的文本-
{text}

-处理指令-
1.  通读全文，理解其内容与场景。
2.  识别出现的角色类型（例如：系统管理员、访客、审计员等）。
3.  **关键步骤 - 同一实体识别**：仔细分析每个角色类型下的所有描述，判断哪些描述指向同一个体：
   - 寻找专有名称（如人名、编号）作为唯一标识符
   - 分析上下文连贯性，识别同一个体的不同描述方式
   - 注意修饰词和属性描述通常不会创造新个体，而是对现有个体的进一步描述
4.  对于每种类型，基于步骤3的分析，确定真正独立的个体数量。
5.  在reasoning字段中，详细说明你的判断依据，特别是如何区分同一个体的不同描述。

-输出格式-
请返回一个包含你的分析和结论的JSON对象：
{{
  "reasoning": "你的判断逻辑",
  "character_counts": {{
    "角色类型1": 数量1,
    "角色类型2": 数量2
  }}
}}

-示例演示-
输入文本（《系统分析说明书》节选）：
  “本系统涉及三类用户：系统管理员（Admin‑A、Admin‑B）、普通用户（User‑001 至 User‑050），以及审计员（Auditor‑Z）。管理员负责配置系统；普通用户进行日常操作；审计员定期审查日志。”

示例输出：
{{
  "reasoning": "文档明确列出 Admin‑A 和 Admin‑B 两名管理员，User‑001 至 User‑050 共 50 名普通用户，以及 1 名审计员。",
  "character_counts": {{
    "系统管理员": 2,
    "普通用户": 50,
    "审计员": 1
  }}
}}
"""

# ---------------------------------------------------------------------------

CONTEXT_AWARE_ENTITY_LINKING_PROMPT = """-任务目标-
你是一个实体链接专家。你的任务是分析一个实体名称列表，并将指向同一个真实世界物体的不同名称（别名）链接到一个统一的"标准名"。

-重要上下文（预分析结论）-
根据对文档的预先分析，我们确定角色的数量如下。请将此作为你判断的"黄金准则"：
{character_analysis}

-待链接的实体列表-
{entities}

-处理指令-
1.  **严格遵守上述上下文结论**。根据角色类型的数量限制，将所有指向同一类型同一个体的不同描述链接到同一个标准名。
2.  **系统性分析步骤**：
   - 首先识别专有名称（人名、编号等）作为实体的核心标识
   - 然后分析描述性词汇（形容词、通用名词）是否指向已识别的专有名称实体
   - 检查语义相关性和上下文一致性
   - 考虑修饰词层次关系（如"高个子学生"可能是对某个具名学生的描述）
3.  为每一组别名，选择一个最完整、最明确的名称作为该组的"标准名"。**如果存在专有名称（如人名、地名），优先选择它作为标准名。**
4.  **验证步骤**：确保链接结果符合上下文给出的数量限制。
5.  最终输出必须是一个JSON对象，其中每个输入实体都作为key，其对应的"标准名"作为value。

-输出格式-
请返回一个JSON对象，格式为 {{ "别名": "标准名", ... }}:
{{
  "alias_map": {{
    "别名1": "标准名A",
    "别名2": "标准名A",
    ...
  }}
}}

-示例演示-
上下文（示例）：
  {{
    "character_counts": {{
      "系统管理员": 2,
      "普通用户": 3
    }}
  }}

待链接实体：
  ["Admin‑A","管理员A","系统管理员A","Admin‑B","管理员B","User‑001","U‑1","User‑002","User‑003"]

示例输出：
{{
  "alias_map": {{
    "Admin‑A": "Admin‑A",
    "管理员A": "Admin‑A",
    "系统管理员A": "Admin‑A",
    "Admin‑B": "Admin‑B",
    "管理员B": "Admin‑B",
    "User‑001": "User‑001",
    "U‑1": "User‑001",
    "User‑002": "User‑002",
    "User‑003": "User‑003"
  }}
}}
"""


# =============================================================================
# --- CONFIGURATION AND CLIENT SETUP (UNCHANGED) ---
# =============================================================================
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-plus")
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 优先检查 DashScope，如果都没有则提示
if not DASHSCOPE_API_KEY and not OPENAI_API_KEY:
    raise ValueError("请设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY 环境变量")
DEFAULT_DATA_DIR = Path("examples/demo_outputs")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

def get_llm_client() -> Any:
    """获取 LLM 客户端，优先使用 DashScope"""
    if OpenAI is None:
        raise RuntimeError("The 'openai' Python SDK is not installed. Please run 'pip install openai'.")
    
    # 优先使用 DashScope
    if DASHSCOPE_API_KEY:
        api_key, base_url = DASHSCOPE_API_KEY, "https://dashscope.aliyuncs.com/compatible-mode/v1"
        print(f"✅ Using DashScope API with model: {LLM_MODEL}")
    elif OPENAI_API_KEY:
        api_key, base_url = OPENAI_API_KEY, None
        print(f"✅ Using OpenAI API with model: {LLM_MODEL}")
    else:
        raise ValueError("请设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY 环境变量")
    
    return OpenAI(api_key=api_key, base_url=base_url)

# =============================================================================
# --- CORE LOGIC CLASSES (UPDATED) ---
# =============================================================================
class InformationExtractor:
    """Encapsulates LLM calls, now including a role analysis step."""
    def __init__(self, client: Any, log_dir: Optional[Path] = None):
        self.client = client
        self.model = LLM_MODEL
        self.log_dir = log_dir or DEFAULT_DATA_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup unified logging
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup unified logger for the pipeline."""
        logger = logging.getLogger(f"KnowledgeGraph_{self.timestamp}")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        log_file = self.log_dir / f"pipeline_log_{self.timestamp}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        print(f"📋 Unified pipeline log: {log_file}")
        return logger

    def _log_step(self, step_name: str, data: Dict[str, Any]) -> None:
        """Log step information in a structured format."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"STEP: {step_name}")
        self.logger.info(f"{'='*60}")
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                self.logger.info(f"{key}:\n{json.dumps(value, ensure_ascii=False, indent=2)}")
            else:
                self.logger.info(f"{key}: {value}")

    def _call_llm(self, prompt: str, task_name: str) -> Dict[str, Any]:
        print(f"    🤖 Sending request to LLM for: {task_name}...")
        
        # Log the request
        self.logger.info(f"\n--- LLM REQUEST: {task_name} ---")
        self.logger.info(f"Prompt:\n{prompt}")
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}],
                temperature=0.0, response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            print(f"    ✅ LLM response received for {task_name}.")
            
            # Log the response
            self.logger.info(f"Response:\n{content}")
            self.logger.info(f"--- END LLM REQUEST: {task_name} ---\n")
            
            return json.loads(content) if content else {}
        except Exception as e:
            print(f"    ❌ [Error] LLM call for {task_name} failed: {e}")
            self.logger.error(f"LLM call failed for {task_name}: {str(e)}")
            return {}

    def extract_candidates(self, text: str) -> Tuple[Dict, List]:
        # (Unchanged)
        full_prompt = f"{FREE_EXTRACTION_PROMPT}\n\n文本:\n---\n{text}\n---"
        response_data = self._call_llm(full_prompt, "Candidate Extraction")
        entities, triples = self._parse_extraction_output(response_data)
        
        # Save intermediate results
        candidates_data = {
            "input_text": text,
            "extracted_entities": entities,
            "extracted_triples": triples,
            "entity_count": len(entities),
            "triple_count": len(triples)
        }
        self._log_step("candidates_extraction", candidates_data)
        
        return entities, triples

    def optimize_ontology(self, entities: Dict, relations: List) -> Dict:
        # (Unchanged)
        entities_info = [f"- {name} (类型: {data.get('type', 'N/A')})" for name, data in entities.items()]
        relations_info = [f"- {rel.get('subject')} --{rel.get('predicate')}--> {rel.get('object')}" for rel in relations]
        prompt = SCHEMA_OPTIMIZATION_PROMPT.format(entities='\n'.join(entities_info), relations='\n'.join(relations_info))
        response_data = self._call_llm(prompt, "Schema Optimization")
        
        # Save intermediate results
        optimization_data = {
            "input_entities": entities,
            "input_relations": relations,
            "optimized_schema": response_data,
            "entity_types_optimized": response_data.get("entities", []),
            "relation_types_optimized": response_data.get("relations", []),
            "attribute_types_optimized": response_data.get("attributes", [])
        }
        self._log_step("schema_optimization", optimization_data)
        
        return response_data

    def refine_and_relabel(self, triples: List, schema: Dict) -> List:
        # (Unchanged)
        prompt = REFINE_AND_RELABEL_PROMPT.format(
            triples=json.dumps(triples, ensure_ascii=False, indent=2),
            schema=json.dumps(schema, ensure_ascii=False, indent=2)
        )
        response_data = self._call_llm(prompt, "Refinement and Relabeling")
        refined_triples = response_data.get("refined_triples", [])
        valid_triples = [t for t in refined_triples if isinstance(t, dict) and all(k in t for k in ['subject', 'predicate', 'object'])]
        
        # Save intermediate results
        refinement_data = {
            "input_triples": triples,
            "input_schema": schema,
            "raw_refined_triples": refined_triples,
            "valid_refined_triples": valid_triples,
            "input_count": len(triples),
            "output_count": len(valid_triples),
            "filtered_count": len(refined_triples) - len(valid_triples)
        }
        self._log_step("refinement_and_relabeling", refinement_data)
        
        return valid_triples

    def analyze_roles(self, text: str) -> Dict:
        """NEW METHOD: Performs high-level role analysis."""
        prompt = ROLE_ANALYSIS_PROMPT.format(text=text)
        response_data = self._call_llm(prompt, "Role Analysis")
        
        # Save intermediate results
        role_analysis_data = {
            "input_text": text,
            "analysis_result": response_data,
            "reasoning": response_data.get("reasoning", ""),
            "character_counts": response_data.get("character_counts", {})
        }
        self._log_step("role_analysis", role_analysis_data)
        
        return response_data

    def link_entities(self, entity_names: List[str], character_analysis: Dict) -> Dict[str, str]:
        """UPDATED METHOD: Now uses context for linking."""
        prompt = CONTEXT_AWARE_ENTITY_LINKING_PROMPT.format(
            entities=json.dumps(entity_names, ensure_ascii=False),
            character_analysis=json.dumps(character_analysis, ensure_ascii=False, indent=2)
        )
        response_data = self._call_llm(prompt, "Context-Aware Entity Linking")
        alias_map = response_data.get("alias_map", {})
        
        # Save intermediate results
        linking_data = {
            "input_entity_names": entity_names,
            "character_analysis_context": character_analysis,
            "raw_response": response_data,
            "alias_map": alias_map,
            "linking_pairs": len([k for k, v in alias_map.items() if k != v])
        }
        self._log_step("entity_linking", linking_data)
        
        return alias_map

    def _parse_extraction_output(self, data: Dict) -> Tuple[Dict, List]:
        """解析LLM输出，处理实体（包含属性）和关系"""
        if not isinstance(data, dict): return {}, []
        
        raw_entities = data.get("entities", [])
        raw_relations = data.get("relations", [])
        
        # 处理实体（包括属性）
        entities = {}
        for e in raw_entities:
            if isinstance(e, dict) and 'name' in e:
                entity_name = e['name']
                entity_data = {
                    'name': entity_name,
                    'type': e.get('type', '未知'),
                    'description': e.get('description', ''),
                    'attributes': e.get('attributes', {})
                }
                entities[entity_name] = entity_data
        
        # 处理关系（只保留实体间的关系）
        triples = []
        for r in raw_relations:
            if isinstance(r, dict) and all(k in r for k in ['subject', 'predicate', 'object']):
                triples.append(r)
        
        print(f"    📊 Parsed: {len(entities)} entities, {len(triples)} triples")
        return entities, triples

class KnowledgeGraph:
    # (This class is unchanged from the previous version)
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # 支持多重边，防止关系覆盖

    def build_from_entities_and_triples(self, entities: Dict, triples: List[Dict]):
        """从实体（包含属性）和三元组构建图谱"""
        # 先添加所有实体节点（包含属性信息）
        for entity_name, entity_data in entities.items():
            attributes = entity_data.get('attributes', {})
            self.graph.add_node(
                entity_name, 
                type=entity_data.get('type', '未知'),
                description=entity_data.get('description', ''),
                **attributes  # 将属性作为节点属性存储
            )
        
        # 然后添加关系边
        for triple in triples:
            sub, pred, obj = triple.get('subject'), triple.get('predicate'), triple.get('object')
            if not all([sub, pred, obj]): 
                continue
            
            # 通用过滤：去除无意义的关系
            if self._should_filter_relation(str(sub), str(pred), str(obj)):
                continue
            
            # 确保主语和宾语都是实体（而非属性值）
            if sub in entities and obj in entities:
                self.graph.add_edge(sub, obj, predicate=pred)

    def build_from_triples(self, triples: List[Dict]):
        """兼容性方法：仅从三元组构建图谱"""
        for triple in triples:
            sub, pred, obj = triple.get('subject'), triple.get('predicate'), triple.get('object')
            if not all([sub, pred, obj]): 
                continue
            
            # 通用过滤：去除无意义的关系
            if self._should_filter_relation(str(sub), str(pred), str(obj)):
                continue
                
            self.graph.add_node(sub, type='未知')
            self.graph.add_node(obj, type='未知')
            self.graph.add_edge(sub, obj, predicate=pred)
    
    def _should_filter_relation(self, subject: str, predicate: str, object: str) -> bool:
        """通用关系过滤器，去除无意义的关系"""
        # 过滤自环关系（主语和宾语相同）
        if subject == object:
            return True
        
        # 过滤无意义的"是"关系（通常表示类型归属，不是实体间关系）
        if predicate.lower() in ['是', 'is', 'be', '属于', 'belong']:
            return True
            
        # 过滤空关系或过短关系
        if len(predicate.strip()) <= 1:
            return True
            
        return False

    def apply_entity_mapping(self, mapping: Dict[str, str]):
        nodes_to_remove = {alias for alias, canonical in mapping.items() if alias != canonical and alias in self.graph}
        nx.relabel_nodes(self.graph, mapping, copy=False)
        print(f"    🔗 Merged {len(nodes_to_remove)} alias nodes into their canonical forms.")

    def assess_quality(self) -> Dict[str, Any]:
        """Enhanced quality assessment with detailed diagnostics."""
        assessment = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "issues": [],
            "warnings": [],
            "stats": {}
        }
        
        if assessment["total_nodes"] == 0:
            assessment["issues"].append("图谱为空，没有任何节点")
            return assessment
            
        # 1. Check isolated nodes
        isolated_nodes = list(nx.isolates(self.graph))
        if isolated_nodes:
            assessment["issues"].append(f"发现 {len(isolated_nodes)} 个孤立节点（无连接）")
            assessment["stats"]["isolated_nodes"] = len(isolated_nodes)
        
        # 2. Check self-loops
        self_loops = list(nx.selfloop_edges(self.graph))
        if self_loops:
            assessment["warnings"].append(f"发现 {len(self_loops)} 个自环关系")
            assessment["stats"]["self_loops"] = len(self_loops)
        
        # 3. Entity type distribution
        node_types = nx.get_node_attributes(self.graph, "type")
        type_counts = {}
        for node_type in node_types.values():
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        assessment["stats"]["entity_type_distribution"] = type_counts
        
        # 4. Relation type distribution
        edge_predicates = nx.get_edge_attributes(self.graph, "predicate")
        predicate_counts = {}
        for predicate in edge_predicates.values():
            predicate_counts[predicate] = predicate_counts.get(predicate, 0) + 1
        assessment["stats"]["relation_type_distribution"] = predicate_counts
        
        # 5. Check connectivity
        if not nx.is_weakly_connected(self.graph):
            components = list(nx.weakly_connected_components(self.graph))
            assessment["warnings"].append(f"图谱不完全连通，有 {len(components)} 个连通分量")
            assessment["stats"]["connected_components"] = len(components)
        
        # 6. Calculate density
        if assessment["total_nodes"] > 1:
            density = nx.density(self.graph)
            assessment["stats"]["graph_density"] = round(density, 4)
            if density < 0.1:
                assessment["warnings"].append("图谱密度较低，可能存在连接不足的问题")
        
        return assessment

    def print_quality_report(self, title: str):
        """Print enhanced quality assessment report."""
        assessment = self.assess_quality()
        
        print(f"\n  📊 {title} 质量评估报告:")
        print(f"    📈 基本统计: {assessment['total_nodes']} 个节点, {assessment['total_edges']} 条边")
        
        if assessment.get("stats", {}).get("graph_density"):
            print(f"    🔗 图谱密度: {assessment['stats']['graph_density']}")
        
        if assessment.get("stats", {}).get("entity_type_distribution"):
            print(f"    📋 实体类型分布:")
            for etype, count in assessment["stats"]["entity_type_distribution"].items():
                print(f"      - {etype}: {count}")
        
        if assessment.get("stats", {}).get("relation_type_distribution"):
            print(f"    🔗 关系类型分布:")
            for rtype, count in assessment["stats"]["relation_type_distribution"].items():
                print(f"      - {rtype}: {count}")
        
        if assessment["issues"]:
            print(f"    ❌ 发现问题:")
            for issue in assessment["issues"]:
                print(f"      - {issue}")
        
        if assessment["warnings"]:
            print(f"    ⚠️ 注意事项:")
            for warning in assessment["warnings"]:
                print(f"      - {warning}")
        
        if not assessment["issues"] and not assessment["warnings"]:
            print(f"    ✅ 质量检查通过，未发现明显问题")

    def visualize(self, title: str, save_path: Path):
        """Enhanced interactive visualization using Pyvis."""
        if self.graph.number_of_nodes() == 0:
            print("  ⚠️ Graph is empty, skipping visualization.")
            return

        # Create a pyvis Network object with enhanced settings
        net = Network(
            height="600px", 
            width="100%", 
            bgcolor="#222222", 
            directed=True
        )
        
        # Get node types for color grouping
        type_attr = nx.get_node_attributes(self.graph, "type")
        unique_types = sorted(list(set(type_attr.values())))
        
        # Enhanced color scheme for different entity types
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57", "#FF9FF3", "#54A0FF", "#5F27CD"]
        type_color_map = {etype: colors[i % len(colors)] for i, etype in enumerate(unique_types)}
        
        # Add nodes with enhanced styling
        for node in self.graph.nodes():
            node_type = type_attr.get(node, "未知")
            color = type_color_map.get(node_type, "#CCCCCC")
            
            # 获取节点的所有属性
            node_data = self.graph.nodes[node]
            attributes_info = []
            for key, value in node_data.items():
                if key not in ['type', 'description']:  # 排除基本字段
                    attributes_info.append(f"{key}: {value}")
            
            # Create enhanced hover information
            hover_parts = [f"节点: {node}", f"类型: {node_type}"]
            if node_data.get('description'):
                hover_parts.append(f"描述: {node_data['description']}")
            if attributes_info:
                hover_parts.append("属性:")
                hover_parts.extend([f"  • {attr}" for attr in attributes_info])
            
            hover_info = "\\n".join(hover_parts)
            
            net.add_node(
                node, 
                label=str(node),
                title=hover_info,
                color=color,
                size=25,
                font={'size': 14, 'color': 'white', 'bold': True}
            )
        
        # Add edges with relationship labels
        for u, v, data in self.graph.edges(data=True):
            predicate = data.get('predicate', '关系')
            hover_info = f"{u} --[{predicate}]--> {v}"
            
            net.add_edge(
                u, v,
                title=hover_info,
                label=predicate,
                color={'color': '#AAAAAA', 'highlight': '#FF6B6B'},
                width=2,
                arrows={'to': {'enabled': True, 'scaleFactor': 1.2}},
                font={'size': 10, 'color': 'yellow', 'strokeWidth': 2, 'strokeColor': 'black'}
            )
        
        # Configure physics and layout
        net.set_options("""
        var options = {
            "physics": {
                "enabled": true,
                "stabilization": {
                    "enabled": true,
                    "iterations": 100
                },
                "barnesHut": {
                    "gravitationalConstant": -8000,
                    "centralGravity": 0.3,
                    "springLength": 95,
                    "springConstant": 0.04,
                    "damping": 0.09
                }
            },
            "interaction": {
                "hover": true,
                "selectConnectedEdges": true,
                "tooltipDelay": 300
            },
            "layout": {
                "improvedLayout": true
            }
        }
        """)
        
        # Change file extension to .html
        html_path = save_path.with_suffix('.html')
        
        # Save the visualization
        net.save_graph(str(html_path))
        print(f"  🎨 Interactive visualization saved to: {html_path}")

    def save(self, path: Path) -> None:
        """Save knowledge graph to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = nx.node_link_data(self.graph)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 Knowledge graph saved to: {path}")

# =============================================================================
# --- MAIN DEMO PIPELINE (UPDATED) ---
# =============================================================================
def run_demo_pipeline():
    """Executes the 5-step pipeline with Chain-of-Thought reasoning."""
    print("=" * 60); print("===  Knowledge Graph Construction with Chain-of-Thought  ==="); print("=" * 60)
    
    DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    text_path = DEFAULT_DATA_DIR / "sample_text.txt"
    text_content = "苹果公司的CEO蒂姆·库克昨天在加州总部宣布了新产品iPhone 15。这款革命性的智能手机采用了先进的A17芯片，拥有卓越的性能和出色的摄影能力。库克先生对这次发布会非常满意，他表示这是苹果历史上最重要的产品之一。与此同时，苹果的股价在纳斯达克交易所上涨了5%。"
    if not text_path.exists(): text_path.write_text(text_content, encoding="utf-8")
    
    text = text_path.read_text(encoding="utf-8")
    print(f"📄 Processing text: \"{text}\"")
    
    try:
        extractor = InformationExtractor(get_llm_client(), DEFAULT_DATA_DIR)
    except (ValueError, RuntimeError) as e:
        print(f"\n❌ CRITICAL ERROR: Could not initialize LLM client: {e}"); return

    # Log pipeline start
    extractor.logger.info(f"PIPELINE START - Processing text: {text}")

    # --- Step 1: Candidate Extraction ---
    print("\n[Step 1/5] Candidate Extraction...")
    candidate_entities, candidate_triples = extractor.extract_candidates(text)
    if not candidate_triples: print("  ❌ [Fatal] Halting."); return

    # --- Step 2: Schema Optimization ---
    print("\n[Step 2/5] Schema Optimization...")
    optimized_schema = extractor.optimize_ontology(candidate_entities, candidate_triples)
    if not optimized_schema: print("  ⚠️ Schema optimization failed. Halting."); return
    print(f"    📊 Optimized Schema Found: {optimized_schema}")

    # --- Step 3: Refinement & Relabeling ---
    print("\n[Step 3/5] Refinement & Relabeling...")
    refined_triples = extractor.refine_and_relabel(candidate_triples, optimized_schema)
    if not refined_triples: print("  ⚠️ Refinement failed. Halting."); return
    print(f"    ✨ Found {len(refined_triples)} refined triples.")

    # --- Step 4: Role Analysis (Chain-of-Thought) ---
    print("\n[Step 4/5] Role Analysis (Chain-of-Thought)...")
    role_analysis_result = extractor.analyze_roles(text)
    print(f"    🧠 LLM Reasoning: \"{role_analysis_result.get('reasoning', 'N/A')}\"")
    print(f"    🔢 LLM Conclusion: {role_analysis_result.get('character_counts', 'N/A')}")

    # --- Step 5: Context-Aware Entity Linking ---
    print("\n[Step 5/5] Context-Aware Entity Linking...")
    # 使用在步骤1中提取到的所有候选实体名称，而不是精炼后的实体
    all_entity_names = list(candidate_entities.keys())
    entity_alias_map = extractor.link_entities(all_entity_names, role_analysis_result)
    print(f"    🔗 Entity Alias Map Found: {entity_alias_map}")
    
    # --- Final Step: Build & Visualize ---
    print("\n[Final Step] Building and visualizing the final knowledge graph...")
    final_kg = KnowledgeGraph()
    final_kg.build_from_entities_and_triples(candidate_entities, refined_triples)
    
    # Log pre-linking state
    pre_linking_state = {
        "nodes_before_linking": list(final_kg.graph.nodes()),
        "edges_before_linking": [(u, v, data['predicate']) for u, v, data in final_kg.graph.edges(data=True)],
        "quality_before_linking": final_kg.assess_quality()
    }
    extractor._log_step("pre_linking_graph_state", pre_linking_state)
    
    if entity_alias_map: 
        final_kg.apply_entity_mapping(entity_alias_map)
        
        # Log post-linking state
        post_linking_state = {
            "nodes_after_linking": list(final_kg.graph.nodes()),
            "edges_after_linking": [(u, v, data['predicate']) for u, v, data in final_kg.graph.edges(data=True)],
            "quality_after_linking": final_kg.assess_quality(),
            "applied_mappings": entity_alias_map
        }
        extractor._log_step("post_linking_graph_state", post_linking_state)
    
    final_kg.print_quality_report("Final Fused Graph")
    
    # Log final summary
    final_summary = {
        "pipeline_completed": datetime.datetime.now().isoformat(),
        "steps_summary": {
            "step1_candidates": {"entities": len(candidate_entities), "triples": len(candidate_triples)},
            "step2_schema": optimized_schema,
            "step3_refined": {"triples": len(refined_triples)},
            "step4_analysis": role_analysis_result,
            "step5_linking": {"alias_map": entity_alias_map, "linking_pairs": len([k for k, v in entity_alias_map.items() if k != v])}
        },
        "final_graph": {
            "nodes": list(final_kg.graph.nodes()),
            "edges": [(u, v, data['predicate']) for u, v, data in final_kg.graph.edges(data=True)],
            "quality_assessment": final_kg.assess_quality()
        }
    }
    extractor._log_step("pipeline_final_summary", final_summary)
    
    print("\n🔗 Final Triples in Graph:")
    for sub, obj, data in final_kg.graph.edges(data=True):
        print(f"    - {sub} --[{data['predicate']}]--> {obj}")

    final_kg.visualize("Knowledge Graph with Chain-of-Thought", DEFAULT_DATA_DIR / "knowledge_graph.html")
    final_kg.save(DEFAULT_DATA_DIR / "knowledge_graph.json")
    print("\n✅ Demo pipeline completed successfully!")

if __name__ == "__main__":
    run_demo_pipeline() 