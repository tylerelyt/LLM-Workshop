# Exercise 1: Build a two-stage RAG pipeline

Open [lab.py](lab.py) and execute its `# %%` cells in order. It is a self-contained file: sample documents, API calls, indexing, retrieval, reranking, prompt assembly, and generation are all visible in one place. It uses only the Python standard library; no repository imports, package installation, external data files, or local models are required.

## Run

Set `DASHSCOPE_API_KEY` in your terminal environment, then run:

```bash
python workshops/rag/reranker/lab.py
```

In VS Code, use **Run Cell** or **Run Above** to inspect intermediate values. The script also works when copied outside this repository. Executing cells that call model APIs incurs usage charges.

## Cells

1. Configure the three DashScope models and the question; inspect the synthetic documents.
2. Split documents, create embeddings, and keep vectors alongside source passages in memory.
3. Embed the question and retrieve candidates using cosine similarity.
4. Rerank candidates with the dedicated ranking model and inspect the selected passages.
5. Insert passages into `{retrieved_context}` and the question into `{question}`; inspect the complete prompt.
6. Generate and display the answer. Inspect `RESULT` and `USAGE`.

All model calls use DashScope: `text-embedding-v4`, `qwen3-rerank`, and `deepseek-v4.1-flash`. Change `QUESTION`, `RETRIEVE_K`, or `KEEP_K`, then rerun from the relevant cell. The teaching index is rebuilt when the indexing cell runs; it is not a persistent vector database. Reranker scores and cosine similarity have different meanings and should not be compared numerically.

Inspect whether the answer is supported by the selected passages and whether the displayed source references are correct. The script displays the answer for inspection; it does not certify its factual correctness.

The course-wide runner also invokes this same file with `python -m workshops.rag reranker --live`. Without `--live`, the runner only reads a historical snapshot; it does not execute these cells.

## Read the execution log

Output is grouped into six numbered stages with elapsed-time prefixes. Every API request logs its model, start, completion, duration, and token usage. Indexing shows source passages and a five-value vector preview. Retrieval shows candidate ranks and cosine scores; reranking shows old-to-new ranks and excluded passages. Prompt assembly prints both the unfilled template and the exact filled prompt, followed by the generated answer and per-model usage totals. Credentials and full embedding arrays are never logged.

To display and save the same run:

```bash
mkdir -p workshops/rag/results
python -u workshops/rag/reranker/lab.py | tee workshops/rag/results/execution.log
```

The log contains the sample source passages, question, prompt, and answer. If you replace teaching data with private data, treat the resulting log accordingly.
