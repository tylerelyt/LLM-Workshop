"""Reuse the packaged Skill's Feishu CLI search in the local MCP demo."""

if __package__:
    from . import check_feishu_access
else:
    import check_feishu_access

from search_documents import search_documents as search_documents
