# Build a RAG knowledge service for your team

Start with chunking, embeddings, indexing, retrieval, reranking, and answer generation. Improve the same pipeline through deduplication, feedback, language routing, and graph exploration, then expose it to your everyday Harness through MCP.

| Stage | Exercise |
|---|---|
| Retrieval and reranking | [Compare evidence coverage](reranker/README.md) |
| Index maintenance | [Semantic deduplication](dedup/README.md) |
| Feedback | [Chunk quality and alignment samples](quality/README.md) |
| Cross-language search | [Language-specific indexes](language/README.md) |
| Progressive retrieval | [Iterative graph exploration](graph/README.md) |
| Harness integration | [Publish RAG through MCP](mcp_harness/README.md) |

## Run

Configure credentials using [DeepSeek setup](../../README-DEEPSEEK.md). Run from the repository root:

```bash
python -m workshops.rag all --output workshops/rag/results/offline.json
python -m workshops.rag all --live --output workshops/rag/results/live.json
python -m workshops.rag reranker --live
python -m workshops.rag mcp --live
```

Replace `all` with `reranker`, `dedup`, `quality`, `language`, `graph`, or `mcp`. The first exercise uses DashScope-hosted DeepSeek Flash for generation. Other exercises retain their existing generation configuration. The first exercise uses DashScope `text-embedding-v4` and `qwen3-rerank`, with DashScope-hosted DeepSeek Flash generating answers. It does not download an embedding model. MCP currently uses local BGE-small; both exercises share [documents.json](documents.json), with source and version metadata. The first exercise builds its small teaching index in memory each time the indexing cell runs. MCP update experiments modify a temporary copy.

Offline reranking replays a previous live snapshot; maintenance exercises use explicitly identified teaching fixtures. Offline MCP still establishes a real stdio connection and BGE index, so dependencies and model files are required. Set `FASTEMBED_CACHE_PATH` for cached models and `HF_HUB_OFFLINE=1` to prevent downloads.

Deduplication and language exercises use lightweight similarity substitutes; graph exploration uses an isolated fixture. Replace these with your production storage and embedding models before evaluating real workloads.

## Inspect the first exercise step by step

```bash
python workshops/rag/reranker/lab.py
```

[The single-file exercise](reranker/lab.py) contains its own sample corpus and six sequential `# %%` cells: configuration, indexing, retrieval, reranking, prompt assembly, and answer generation. It uses only Python's standard library and `DASHSCOPE_API_KEY`. The index stays in memory so every stage is visible while teaching.
