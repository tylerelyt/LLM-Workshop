#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BGE-m3 召回 + BGE-reranker 重排 + LLM 生成答案的 RAG 示例

本示例展示了现代RAG系统的完整流程：
1. 使用BGE-m3进行语义召回
2. 使用BGE-reranker进行精确重排
3. 使用LLM基于重排后的上下文生成最终答案

技术栈：
- BGE-m3: 多语言多粒度嵌入模型
- BGE-reranker: 精确重排序模型  
- DashScope: 通义千问LLM服务
"""

import os
import json
import time
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import logging
from dataclasses import dataclass, field
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from FlagEmbedding import BGEM3FlagModel, FlagReranker
    import dashscope
    from dashscope import Generation
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    logger.error(f"缺少必要的依赖包: {e}")
    logger.error("请安装: pip install FlagEmbedding dashscope numpy langchain langchain-text-splitters")
    exit(1)

@dataclass
class Document:
    """文档数据结构"""
    id: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = field(default=None)
    chunk_id: Optional[str] = field(default=None)  # 文档块ID
    parent_id: Optional[str] = field(default=None)  # 父文档ID
    chunk_index: Optional[int] = field(default=None)  # 块索引

@dataclass
class RetrievalResult:
    """检索结果数据结构"""
    document: Document
    score: float
    rank: int

class BGERetrievalSystem:
    """基于BGE-m3的检索系统"""
    
    def __init__(self, model_path: str = "BAAI/bge-m3"):
        """
        初始化BGE-m3检索系统
        
        Args:
            model_path: BGE-m3模型路径
        """
        logger.info(f"Loading BGE-m3 model: {model_path}")
        try:
            self.model = BGEM3FlagModel(model_path, use_fp16=True)
            logger.info("BGE-m3 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load BGE-m3 model: {e}")
            raise
            
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None
        
    def add_documents(self, documents: List[Document]):
        """添加文档到检索系统，包含文档切片"""
        logger.info(f"Adding {len(documents)} documents to retrieval system")
        
        # 初始化文档切片器
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # 每个块的最大字符数
            chunk_overlap=200,  # 块之间的重叠字符数
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ";", "；", ":", "：", ".", " ", ""]
        )
        
        # 存储所有文档块
        all_chunks = []
        
        for doc in documents:
            logger.info(f"Splitting document: {doc.title}")
            
            # 对文档内容进行切片
            chunks = text_splitter.split_text(doc.content)
            
            for i, chunk_content in enumerate(chunks):
                chunk_doc = Document(
                    id=f"{doc.id}_chunk_{i}",
                    title=doc.title,  # 保持原标题
                    content=chunk_content,
                    metadata=doc.metadata,
                    chunk_id=f"{doc.id}_chunk_{i}",
                    parent_id=doc.id,
                    chunk_index=i
                )
                all_chunks.append(chunk_doc)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        self.documents = all_chunks
        
        # 构建文档文本用于嵌入
        doc_texts = []
        for doc in self.documents:
            # 结合标题和内容，但内容已经是切片后的
            full_text = f"{doc.title}\n\n{doc.content}"
            doc_texts.append(full_text)
        
        # 生成嵌入向量
        logger.info("Generating embeddings...")
        start_time = time.time()
        embedding_result = self.model.encode(
            doc_texts,
            batch_size=12,
            max_length=8192,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False
        )
        
        # 处理BGE-m3的返回结果
        if isinstance(embedding_result, dict) and 'dense_vecs' in embedding_result:
            self.embeddings = np.array(embedding_result['dense_vecs'])
        else:
            # 如果直接返回向量数组
            self.embeddings = np.array(embedding_result)
        
        embedding_time = time.time() - start_time
        logger.info(f"Generated embeddings for {len(documents)} documents in {embedding_time:.2f}s")
        
    def search(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回的文档数量
            
        Returns:
            检索结果列表
        """
        if not self.documents or self.embeddings is None:
            logger.warning("No documents or embeddings available")
            return []
            
        logger.info(f"Searching for query: {query[:50]}...")
        
        # 对查询进行嵌入
        start_time = time.time()
        query_result = self.model.encode(
            [query],
            batch_size=1,
            max_length=8192,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False
        )
        
        # 处理查询嵌入结果
        if isinstance(query_result, dict) and 'dense_vecs' in query_result:
            query_embedding = np.array(query_result['dense_vecs'][0])
        elif isinstance(query_result, (list, np.ndarray)):
            query_embedding = np.array(query_result[0])
        else:
            query_embedding = np.array(query_result)
        
        # 计算相似度
        similarities = np.dot(self.embeddings, query_embedding)
        
        # 获取top_k结果
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        search_time = time.time() - start_time
        logger.info(f"Search completed in {search_time:.3f}s")
        
        results = []
        for rank, idx in enumerate(top_indices):
            result = RetrievalResult(
                document=self.documents[idx],
                score=float(similarities[idx]),
                rank=rank + 1
            )
            results.append(result)
            
        return results

class BGEReranker:
    """基于BGE-reranker的重排序系统"""
    
    def __init__(self, model_path: str = "BAAI/bge-reranker-v2-m3"):
        """
        初始化BGE重排序器
        
        Args:
            model_path: BGE-reranker模型路径
        """
        logger.info(f"Loading BGE-reranker model: {model_path}")
        try:
            self.reranker = FlagReranker(model_path, use_fp16=True)
            logger.info("BGE-reranker model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load BGE-reranker model: {e}")
            raise
    
    def rerank(self, query: str, results: List[RetrievalResult], top_k: int = 5) -> List[RetrievalResult]:
        """
        重排序检索结果
        
        Args:
            query: 查询文本
            results: 初始检索结果
            top_k: 返回的重排后结果数量
            
        Returns:
            重排后的结果列表
        """
        if not results:
            return []
            
        logger.info(f"Reranking {len(results)} results...")
        
        # 准备输入对
        sentence_pairs = []
        for result in results:
            # 对于切片后的文档，使用块内容进行重排序
            doc_text = f"{result.document.title}\n\n{result.document.content}"
            # 如果是文档块，可以添加块信息
            if result.document.chunk_id:
                doc_text = f"{result.document.title} (块 {result.document.chunk_index})\n\n{result.document.content}"
            sentence_pairs.append([query, doc_text])
        
        # 进行重排序
        start_time = time.time()
        scores = self.reranker.compute_score(sentence_pairs, batch_size=8)
        rerank_time = time.time() - start_time
        
        logger.info(f"Reranking completed in {rerank_time:.3f}s")
        
        # 创建新的结果列表
        reranked_results = []
        for i, score in enumerate(scores):
            result = results[i]
            reranked_result = RetrievalResult(
                document=result.document,
                score=float(score),
                rank=i + 1
            )
            reranked_results.append(reranked_result)
        
        # 按重排序分数排序
        reranked_results.sort(key=lambda x: x.score, reverse=True)
        
        # 更新排名
        for i, result in enumerate(reranked_results[:top_k]):
            result.rank = i + 1
            
        return reranked_results[:top_k]

class LLMGenerator:
    """基于DashScope的答案生成器"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-max"):
        """
        初始化LLM生成器
        
        Args:
            api_key: DashScope API密钥
            model: 模型名称
        """
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量或传入api_key参数")
            
        dashscope.api_key = self.api_key
        logger.info(f"LLM Generator initialized with model: {model}")
    
    def generate_answer(self, query: str, contexts: List[RetrievalResult]) -> Dict[str, Any]:
        """
        基于检索上下文生成答案
        
        Args:
            query: 用户查询
            contexts: 重排后的上下文文档
            
        Returns:
            生成结果包含答案和元数据
        """
        if not contexts:
            return {
                "answer": "抱歉，我没有找到相关的信息来回答您的问题。",
                "sources": [],
                "confidence": 0.0
            }
        
        # 构建上下文文本
        context_texts = []
        sources = []
        
        for i, result in enumerate(contexts):
            doc = result.document
            
            # 构建参考资料信息，包含块信息
            title_info = doc.title
            if doc.chunk_id and doc.chunk_index is not None:
                title_info = f"{doc.title} (第{doc.chunk_index + 1}块)"
            
            context_texts.append(
                f"参考资料{i+1}：\n"
                f"标题：{title_info}\n"
                f"内容：{doc.content}\n"
                f"相关性评分：{result.score:.3f}\n"
            )
            sources.append({
                "title": title_info,
                "score": result.score,
                "rank": result.rank,
                "chunk_id": doc.chunk_id,
                "parent_id": doc.parent_id
            })
        
        context_str = "\n" + "="*50 + "\n".join(context_texts)
        
        # 构建提示词
        prompt = f"""你是一个专业的AI助手，请基于提供的参考资料回答用户的问题。

用户问题：{query}

参考资料：
{context_str}

请按照以下要求回答：
1. 基于参考资料中的信息进行回答，确保准确性
2. 如果参考资料中没有直接答案，请诚实说明
3. 在回答中适当引用参考资料的关键信息
4. 保持回答的逻辑性和条理性
5. 使用简洁明了的语言

回答："""

        logger.info("Generating answer with LLM...")
        start_time = time.time()
        
        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3,
                top_p=0.8,
                repetition_penalty=1.05
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Answer generated in {generation_time:.2f}s")
            
            # 处理DashScope响应
            if hasattr(response, 'status_code') and response.status_code == 200:
                answer = response.output.text.strip()
                
                # 评估置信度（基于上下文相关性）
                avg_score = sum(r.score for r in contexts) / len(contexts)
                confidence = min(avg_score * 0.8, 0.95)  # 归一化到合理范围
                
                return {
                    "answer": answer,
                    "sources": sources,
                    "confidence": confidence,
                    "generation_time": generation_time,
                    "context_count": len(contexts)
                }
            else:
                error_msg = getattr(response, 'message', 'Unknown error')
                logger.error(f"LLM generation failed: {error_msg}")
                return {
                    "answer": "抱歉，生成答案时出现错误，请稍后重试。",
                    "sources": sources,
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return {
                "answer": "抱歉，生成答案时出现错误，请稍后重试。",
                "sources": sources,
                "confidence": 0.0
            }

class RAGPipeline:
    """完整的RAG流水线"""
    
    def __init__(self, 
                 retrieval_model: str = "BAAI/bge-m3",
                 reranker_model: str = "BAAI/bge-reranker-v2-m3",
                 llm_model: str = "qwen-max"):
        """
        初始化RAG流水线
        
        Args:
            retrieval_model: 检索模型路径
            reranker_model: 重排序模型路径
            llm_model: LLM模型名称
        """
        logger.info("Initializing RAG Pipeline...")
        
        self.retrieval_system = BGERetrievalSystem(retrieval_model)
        self.reranker = BGEReranker(reranker_model)
        self.llm_generator = LLMGenerator(model=llm_model)
        
        logger.info("RAG Pipeline initialized successfully")
    
    def load_documents(self, documents: List[Document]):
        """加载文档到检索系统"""
        self.retrieval_system.add_documents(documents)
    
    def query(self, 
             question: str,
             retrieval_top_k: int = 20,
             rerank_top_k: int = 5) -> Dict[str, Any]:
        """
        执行完整的RAG查询流程
        
        Args:
            question: 用户问题
            retrieval_top_k: 检索阶段返回的文档数量
            rerank_top_k: 重排序后保留的文档数量
            
        Returns:
            完整的查询结果
        """
        logger.info(f"Processing RAG query: {question[:50]}...")
        total_start_time = time.time()
        
        # 步骤1: BGE-m3检索
        logger.info("Step 1: BGE-m3 Retrieval...")
        retrieval_results = self.retrieval_system.search(question, retrieval_top_k)
        
        if not retrieval_results:
            return {
                "question": question,
                "answer": "抱歉，没有找到相关文档。",
                "sources": [],
                "confidence": 0.0,
                "pipeline_stats": {
                    "retrieval_count": 0,
                    "rerank_count": 0,
                    "total_time": time.time() - total_start_time
                }
            }
        
        logger.info(f"Retrieved {len(retrieval_results)} documents")
        
        # 步骤2: BGE-reranker重排序
        logger.info("Step 2: BGE-reranker Reranking...")
        reranked_results = self.reranker.rerank(question, retrieval_results, rerank_top_k)
        logger.info(f"Reranked to top {len(reranked_results)} documents")
        
        # 步骤3: LLM生成答案
        logger.info("Step 3: LLM Answer Generation...")
        generation_result = self.llm_generator.generate_answer(question, reranked_results)
        
        total_time = time.time() - total_start_time
        
        # 整合结果
        result = {
            "question": question,
            "answer": generation_result["answer"],
            "sources": generation_result["sources"],
            "confidence": generation_result["confidence"],
            "pipeline_stats": {
                "retrieval_count": len(retrieval_results),
                "rerank_count": len(reranked_results),
                "total_time": total_time,
                "generation_time": generation_result.get("generation_time", 0)
            }
        }
        
        logger.info(f"RAG query completed in {total_time:.2f}s")
        return result

def load_sample_documents() -> List[Document]:
    """加载示例文档数据"""
    
    # 检查是否有示例数据文件
    data_file = Path("sample_documents.json")
    if data_file.exists():
        logger.info("Loading documents from sample_documents.json")
        with open(data_file, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
            return [Document(**doc) for doc in doc_data]
    
    # 如果没有数据文件，使用内置示例
    logger.info("Using built-in sample documents")
    
    sample_docs = [
        Document(
            id="doc_001",
            title="Python编程基础 - 变量和数据类型",
            content="""Python是一种高级编程语言，具有简洁的语法和强大的功能。在Python中，变量用于存储数据，不需要声明变量类型。Python支持多种数据类型：

1. 数字类型：
   - int（整数）：如 42, -17, 0
   - float（浮点数）：如 3.14, -0.001, 2.0
   - complex（复数）：如 3+4j, 1-2j

2. 字符串类型（str）：
   - 使用单引号或双引号定义：'hello' 或 "world"
   - 支持转义字符：\n（换行）, \t（制表符）
   - 支持格式化：f"Hello {name}"

3. 布尔类型（bool）：
   - True 和 False
   - 通常用于条件判断

4. 容器类型：
   - list（列表）：有序可变序列 [1, 2, 3]
   - tuple（元组）：有序不可变序列 (1, 2, 3)
   - dict（字典）：键值对映射 {'key': 'value'}
   - set（集合）：无序唯一元素集合 {1, 2, 3}

变量赋值很简单：x = 10, name = "Python", data = [1, 2, 3]"""
        ),
        
        Document(
            id="doc_002", 
            title="Python编程进阶 - 函数和模块",
            content="""函数是Python中组织代码的重要方式，可以提高代码的复用性和可维护性。

函数定义语法：
```python
def function_name(parameters):
    \"\"\"函数说明文档\"\"\"
    # 函数体
    return result  # 可选
```

函数特性：
1. 参数类型：
   - 位置参数：def func(a, b)
   - 默认参数：def func(a, b=10)
   - 可变参数：def func(*args, **kwargs)
   - 关键字参数：def func(a, *, b, c)

2. 返回值：
   - 可以返回单个值、多个值（元组）
   - 没有return语句时返回None

3. 作用域：
   - 局部作用域：函数内部变量
   - 全局作用域：模块级变量
   - 闭包：内层函数访问外层函数变量

模块系统：
- 模块是包含Python代码的文件（.py文件）
- 使用import语句导入模块：import math, from os import path
- 包是包含多个模块的目录，必须有__init__.py文件
- Python标准库提供了丰富的内置模块：os, sys, json, datetime等"""
        ),
        
        Document(
            id="doc_003",
            title="Python面向对象编程 - 类和对象",
            content="""面向对象编程（OOP）是Python的重要特性，通过类和对象来组织代码。

类定义语法：
```python
class ClassName:
    \"\"\"类说明文档\"\"\"
    
    class_variable = "类变量"
    
    def __init__(self, parameters):
        \"\"\"构造方法\"\"\"
        self.instance_variable = parameters
    
    def method_name(self):
        \"\"\"实例方法\"\"\"
        return self.instance_variable
```

OOP核心概念：

1. 封装（Encapsulation）：
   - 将数据和方法组合在类中
   - 使用私有属性（_variable）和方法（_method）
   - 提供公共接口访问内部数据

2. 继承（Inheritance）：
   - 子类继承父类的属性和方法：class Child(Parent)
   - 方法重写：在子类中重新定义父类方法
   - super()函数：调用父类方法

3. 多态（Polymorphism）：
   - 相同接口，不同实现
   - 鸭子类型：如果它看起来像鸭子，叫起来像鸭子，那它就是鸭子

特殊方法（魔术方法）：
- __init__：构造方法
- __str__：字符串表示
- __len__：长度
- __getitem__：索引访问
- __add__：加法运算符重载"""
        ),
        
        Document(
            id="doc_004",
            title="Python数据处理 - NumPy和Pandas",
            content="""NumPy和Pandas是Python数据科学生态系统的核心库。

NumPy（Numerical Python）：
- 提供高性能的多维数组对象ndarray
- 支持广播（broadcasting）机制
- 丰富的数学函数库

NumPy基本用法：
```python
import numpy as np

# 创建数组
arr = np.array([1, 2, 3, 4, 5])
matrix = np.array([[1, 2], [3, 4]])

# 数组操作
arr * 2  # 元素乘法
np.sum(arr)  # 求和
np.mean(arr)  # 平均值
```

Pandas：
- 提供DataFrame和Series数据结构
- 强大的数据读取、清洗、分析功能
- 支持多种数据格式：CSV, Excel, JSON, SQL等

Pandas基本用法：
```python
import pandas as pd

# 创建DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['Beijing', 'Shanghai', 'Guangzhou']
})

# 数据操作
df.head()  # 查看前几行
df.describe()  # 统计描述
df.groupby('city').mean()  # 分组聚合
```

常用数据操作：
- 数据选择：df['column'], df.loc[], df.iloc[]
- 数据过滤：df[df['age'] > 25]
- 数据合并：pd.merge(), pd.concat()
- 数据透视：df.pivot_table()"""
        ),
        
        Document(
            id="doc_005",
            title="机器学习基础 - Scikit-learn入门",
            content="""Scikit-learn是Python最流行的机器学习库，提供了简单高效的数据挖掘和数据分析工具。

主要特性：
- 统一的API设计
- 丰富的算法支持
- 优秀的文档和示例
- 与NumPy、Pandas集成良好

机器学习工作流程：

1. 数据准备：
```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

# 加载数据
data = load_iris()
X, y = data.data, data.target

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
```

2. 模型训练：
```python
from sklearn.ensemble import RandomForestClassifier

# 创建模型
model = RandomForestClassifier(n_estimators=100)

# 训练模型
model.fit(X_train, y_train)
```

3. 模型评估：
```python
from sklearn.metrics import accuracy_score, classification_report

# 预测
y_pred = model.predict(X_test)

# 评估
accuracy = accuracy_score(y_test, y_pred)
print(f"准确率: {accuracy:.3f}")
```

常用算法类别：
- 监督学习：分类（SVM, Random Forest）、回归（Linear Regression）
- 无监督学习：聚类（K-Means）、降维（PCA）
- 模型选择：交叉验证、网格搜索
- 数据预处理：标准化、特征选择"""
        ),
        
        Document(
            id="doc_006",
            title="深度学习框架 - TensorFlow和PyTorch",
            content="""TensorFlow和PyTorch是目前最主流的深度学习框架。

TensorFlow特点：
- Google开发的开源框架
- 生产环境部署友好
- TensorFlow 2.x采用eager execution
- Keras作为高级API

TensorFlow基本用法：
```python
import tensorflow as tf

# 创建简单的神经网络
model = tf.keras.Sequential([
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10, activation='softmax')
])

# 编译模型
model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# 训练模型
model.fit(X_train, y_train, epochs=10, batch_size=32)
```

PyTorch特点：
- Facebook开发的开源框架
- 动态计算图，更灵活
- 研究友好，调试方便
- 强大的自动微分系统

PyTorch基本用法：
```python
import torch
import torch.nn as nn

# 定义神经网络
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 10)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# 创建模型和优化器
model = Net()
optimizer = torch.optim.Adam(model.parameters())
criterion = nn.CrossEntropyLoss()
```

选择建议：
- 研究和原型开发：PyTorch更灵活
- 生产部署：TensorFlow生态更完善
- 学习成本：两者都有丰富的教程和社区支持"""
        ),
        
        Document(
            id="doc_007",
            title="Web开发框架 - Flask和Django",
            content="""Flask和Django是Python最受欢迎的Web开发框架。

Flask特点：
- 轻量级微框架
- 灵活性高，扩展性强
- 最小化核心，按需添加功能
- 适合小到中型项目

Flask基本用法：
```python
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Flask!"

@app.route('/user/<name>')
def user(name):
    return f"Hello, {name}!"

@app.route('/api/data', methods=['POST'])
def api_data():
    data = request.get_json()
    return {'status': 'success', 'data': data}

if __name__ == '__main__':
    app.run(debug=True)
```

Django特点：
- 全功能Web框架
- "电池已包含"哲学
- 强大的ORM系统
- 自动生成管理界面
- 适合大型项目

Django核心组件：
1. 模型（Models）：数据层，定义数据结构
2. 视图（Views）：业务逻辑层，处理请求
3. 模板（Templates）：表现层，生成HTML
4. URL配置：路由系统

Django基本用法：
```python
# models.py
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

# views.py
from django.shortcuts import render
from django.http import JsonResponse

def user_list(request):
    users = User.objects.all()
    return render(request, 'users.html', {'users': users})
```

选择建议：
- 快速原型：Flask更简单
- 复杂应用：Django功能更完整
- 学习曲线：Flask较平缓，Django较陡峭"""
        ),
        
        Document(
            id="doc_008",
            title="数据可视化 - Matplotlib和Plotly",
            content="""数据可视化是数据分析的重要环节，Python提供了多种优秀的可视化库。

Matplotlib：
- Python最基础的绘图库
- 功能全面，可定制性强
- 支持多种输出格式
- 语法相对复杂但功能强大

Matplotlib基本用法：
```python
import matplotlib.pyplot as plt
import numpy as np

# 基本线图
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y, label='sin(x)')
plt.xlabel('X轴')
plt.ylabel('Y轴')
plt.title('正弦函数图')
plt.legend()
plt.grid(True)
plt.show()

# 子图
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(x, np.sin(x))
ax2.plot(x, np.cos(x))
```

Plotly：
- 交互式可视化库
- 支持Web部署
- 美观的默认样式
- 支持3D绘图

Plotly基本用法：
```python
import plotly.graph_objects as go
import plotly.express as px

# 使用Express API（简单）
df = px.data.iris()
fig = px.scatter(df, x="sepal_width", y="sepal_length", 
                color="species", title="鸢尾花数据散点图")
fig.show()

# 使用Graph Objects API（灵活）
fig = go.Figure()
fig.add_trace(go.Scatter(x=[1, 2, 3, 4], y=[10, 11, 12, 13]))
fig.update_layout(title="自定义图表")
fig.show()
```

其他可视化库：
- Seaborn：基于Matplotlib的统计可视化
- Bokeh：交互式Web可视化
- Altair：基于Vega-Lite的声明式可视化

选择建议：
- 静态图表：Matplotlib + Seaborn
- 交互式图表：Plotly或Bokeh
- 快速探索：Pandas内置绘图功能"""
        )
    ]
    
    return sample_docs

def main():
    """主演示函数"""
    print("=" * 60)
    print("🚀 BGE-m3 + BGE-reranker + LLM RAG 演示")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv('DASHSCOPE_API_KEY'):
        print("⚠️  请设置DASHSCOPE_API_KEY环境变量")
        print("   export DASHSCOPE_API_KEY=your_api_key")
        return
    
    try:
        # 初始化RAG系统
        print("\n📋 初始化RAG系统...")
        rag_pipeline = RAGPipeline()
        
        # 加载示例文档
        print("\n📚 加载示例文档...")
        documents = load_sample_documents()
        rag_pipeline.load_documents(documents)
        print(f"✅ 已加载 {len(documents)} 个文档")
        
        # 示例查询
        test_queries = [
            "Python中有哪些数据类型？",
            "如何在Python中定义函数？",
            "Pandas和NumPy有什么区别？",
            "Flask和Django哪个更适合新手？",
            "机器学习的基本流程是什么？"
        ]
        
        print("\n🔍 开始RAG查询演示...")
        print("=" * 60)
        
        for i, query in enumerate(test_queries[:3], 1):  # 演示前3个查询
            print(f"\n【查询 {i}】{query}")
            print("-" * 50)
            
            # 执行RAG查询
            result = rag_pipeline.query(
                question=query,
                retrieval_top_k=10,
                rerank_top_k=3
            )
            
            # 显示结果
            print(f"\n💡 答案：")
            print(result['answer'])
            
            print(f"\n📊 相关性评分：{result['confidence']:.3f}")
            
            print(f"\n📖 参考资料：")
            for j, source in enumerate(result['sources'][:3], 1):
                print(f"  {j}. {source['title']} (评分: {source['score']:.3f})")
            
            stats = result['pipeline_stats']
            print(f"\n⏱️  性能统计：")
            print(f"  检索文档数：{stats['retrieval_count']}")
            print(f"  重排文档数：{stats['rerank_count']}")
            print(f"  总耗时：{stats['total_time']:.2f}秒")
            print(f"  生成耗时：{stats['generation_time']:.2f}秒")
            
            print("=" * 60)
        
        print("\n✅ RAG演示完成！")
        print(f"\n📊 总体统计：")
        print(f"  原始文档数：{len(documents)}")
        print(f"  切片后块数：{len(rag_pipeline.retrieval_system.documents)}")
        print(f"  BGE-m3 + BGE-reranker + LLM 三阶段流水线运行正常")
        print(f"  文档切片功能：✅ 已启用 (chunk_size=1000, overlap=200)")
        print(f"  语义检索：✅ BGE-m3多语言嵌入")
        print(f"  精确重排：✅ BGE-reranker二次排序") 
        print(f"  智能生成：✅ 通义千问qwen-max")
        
    except Exception as e:
        logger.error(f"RAG系统初始化失败: {e}")
        print(f"❌ 系统错误: {e}")

if __name__ == "__main__":
    main() 