"""兼容导入，实现在 workshops.rag 中维护。"""

import sys
from importlib import import_module
import runpy
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    runpy.run_module("workshops.rag.graph.lab", run_name="__main__")
else:
    sys.modules[__name__] = import_module("workshops.rag.graph.lab")
