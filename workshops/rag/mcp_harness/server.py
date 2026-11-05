"""通过 stdio MCP 发布带出处和版本的 RAG 检索。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from workshops.rag.deepseek_workshop import VectorIndex

CORPUS = Path(__file__).resolve().parents[1] / "documents.json"


class Passage(BaseModel):
    citation_id: str
    document_id: str
    title: str
    source: str
    version: str
    text: str
    similarity: float


class SearchResult(BaseModel):
    corpus_revision: str
    passages: list[Passage]


def create_server(corpus: Path, index_directory: Path) -> MCPServer:
    server = MCPServer("rag-knowledge", instructions="读取教学知识库的当前原文，按返回的 citation_id 引用。")
    lock = Lock()
    index = None
    indexed_source = None
    metadata = {}

    @server.tool(structured_output=True, annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False,
    ))
    def search_knowledge(
        query: Annotated[str, Field(min_length=1, max_length=300)],
        top_k: Annotated[int, Field(ge=1, le=5)] = 3,
    ) -> SearchResult:
        """检索与问题相关的当前文档片段。每个候选包含原文、出处、版本和可引用 ID。"""
        nonlocal index, indexed_source, metadata
        if not query.strip():
            raise ToolError("请输入要检索的问题。")
        with lock:
            source = corpus.read_bytes()
            if source != indexed_source:
                documents = json.loads(source)
                current_metadata = {doc["id"]: doc for doc in documents}
                if not documents or len(current_metadata) != len(documents):
                    raise ToolError("知识库必须包含非空且标识唯一的文档。")
                if index is None:
                    index = VectorIndex("BAAI/bge-small-zh-v1.5", index_directory)
                index.build_or_load(source)
                metadata, indexed_source = current_metadata, source
            passages = []
            for hit in index.search(query.strip(), top_k):
                document = metadata[hit["document"]]
                details = document.get("metadata", document)
                passages.append(Passage(
                    citation_id=f"{hit['id']}@{details['version']}",
                    document_id=hit["document"], title=hit["title"],
                    source=details["source"], version=details["version"],
                    text=hit["text"], similarity=hit["retrieval_score"],
                ))
            return SearchResult(corpus_revision=hashlib.sha256(source).hexdigest(), passages=passages)

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="workshop-rag-index-") as directory:
        create_server(args.corpus.resolve(), Path(directory)).run(transport="stdio")


if __name__ == "__main__":
    main()
