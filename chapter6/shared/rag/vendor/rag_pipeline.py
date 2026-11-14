"""兼容旧 Workshop 导入；BGE 实现统一维护在 chapter6/reranking。"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from chapter6.reranking.rag_pipeline import (
    BGERetrievalSystem, BGEReranker, Document, RetrievalResult, LLMGenerator,
)
