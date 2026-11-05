"""课程 RAG 练习入口，与 workshops/rag 共用同一份实现。"""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[2] / 'workshops/rag/deepseek_workshop.py'),
                  run_name='__main__')
