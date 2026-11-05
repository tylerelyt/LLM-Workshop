"""兼容旧 Workshop 导入；BGE 实现统一维护在 chapter3/lesson1。"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from chapter3.lesson1.rag_pipeline import (
    BGERetrievalSystem, BGEReranker, Document, RetrievalResult, LLMGenerator,
)
