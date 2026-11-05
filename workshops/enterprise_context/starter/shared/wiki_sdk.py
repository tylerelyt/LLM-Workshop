"""多个应用共用的 Wiki SDK。课程使用本地快照；这里不访问真实企业。

本轮业务变更只能发生在应用层，此文件是已有公共接口。
"""
from __future__ import annotations

import json
from pathlib import Path


class WikiSDK:
    def __init__(self, data_path: str | Path):
        self.data_path = Path(data_path)

    def _read(self) -> dict:
        return json.loads(self.data_path.read_text(encoding="utf-8"))

    def list_documents(self) -> list[dict]:
        """读取当前文档；page_id 稳定，project_key 和 version 可以变化。"""
        return self._read()["documents"]

    def read_document(self, page_id: str) -> dict:
        for document in self.list_documents():
            if str(document["page_id"]) == str(page_id):
                return document
        raise KeyError(f"文档不存在：{page_id}")

    def list_changes(self, after: int, limit: int = 100) -> dict:
        """按业务游标读取事件。同一个 event_id 可能重复投递。"""
        if after < 0 or limit < 1:
            raise ValueError("游标不能为负，limit 必须大于零")
        remaining = sorted(
            (event for event in self._read()["events"] if event["seq"] > after),
            key=lambda event: event["seq"],
        )
        batch = remaining[:limit]
        return {
            "events": batch,
            "next_cursor": batch[-1]["seq"] if batch else after,
            "has_more": len(remaining) > len(batch),
        }
