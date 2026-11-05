"""现有知识平台：全局检索已经可以工作。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.wiki_sdk import WikiSDK


class KnowledgeApplication:
    def __init__(self, sdk: WikiSDK):
        self.sdk = sdk

    def search(self, query: str) -> dict:
        term = query.casefold()
        documents = self.sdk.list_documents()
        items = [
            {
                "page_id": str(document["page_id"]),
                "title": document["title"],
                "project_key": document["project_key"],
                "version": document["version"],
                "excerpt": document["body"][:90],
            }
            for document in documents
            if term in (document["title"] + "\n" + document["body"]).casefold()
        ]
        return {"items": items}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="查看现有知识平台的全局检索")
    parser.add_argument("--query", default="")
    parser.add_argument("--data", type=Path, default=ROOT / "data/wiki.json")
    args = parser.parse_args()
    result = KnowledgeApplication(WikiSDK(args.data)).search(args.query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
