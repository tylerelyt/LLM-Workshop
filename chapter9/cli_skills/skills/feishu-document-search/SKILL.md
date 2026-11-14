---
name: feishu-document-search
description: 搜索当前用户可访问的飞书文档。用飞书 CLI 按关键词查找，或列出可见文档，并返回标题和链接。
---

使用 `scripts/search_documents.py`。本机需要 Python 3 和已配置飞书应用的 `lark-cli`。

已有授权时运行 `python3 scripts/search_documents.py --list-only --query '关键词'`。浏览文档时省略 `--query`。每次只返回一页，默认 10 条。

当缺少搜索授权时，请用户在能看到实时输出的终端运行同一脚本，去掉 `--list-only`。脚本申请 `search:docs:read`，显示二维码，并在用户确认后继续搜索。把返回的标题和链接交给用户。授权链接和设备码只用于当前授权会话。
