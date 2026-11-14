"""课程 RAG 练习入口，与 chapter6/shared/rag 共用同一份实现。"""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'shared/rag/deepseek_workshop.py'),
                  run_name='__main__')
