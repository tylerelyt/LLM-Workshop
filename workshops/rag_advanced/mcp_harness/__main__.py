"""兼容导入，实现在 workshops.rag 中维护。"""

import sys
from importlib import import_module

_impl = import_module("workshops.rag.mcp_harness.__main__")
if __name__ == "__main__":
    _impl.main()
else:
    sys.modules[__name__] = _impl
