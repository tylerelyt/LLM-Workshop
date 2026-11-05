# Run the workshops with DeepSeek Flash

The RAG, MCP, Skill, and Spec exercises share the official DeepSeek API client. Credentials come from local environment variables. Standalone chapter examples remain available in their own directories.

## Setup

Use Python 3.11 or 3.12 from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-deepseek.lock
cp .env.example .env
```

Set `DEEPSEEK_API_KEY` in the ignored `.env` file, or use `DEEPSEEK_ENV_FILE` to load a file outside the repository. Never include credentials in examples or distribution packages. The default model is `deepseek-flash`; override it with `DEEPSEEK_MODEL`. The default endpoint is `https://api.deepseek.com`.

## RAG: retrieval, maintenance, and Harness integration

See the [RAG workshop](workshops/rag/README.md).

```bash
python -m workshops.rag all --output workshops/rag/results/offline.json
python -m workshops.rag all --live --output workshops/rag/results/live.json
python -m workshops.rag reranker --live
python -m workshops.rag mcp --live
```

The first exercise is a single self-contained file. It includes the sample documents and sequential `# %%` cells for indexing, retrieval, reranking, prompt assembly, and generation:

```bash
python workshops/rag/reranker/lab.py
```

Set `DASHSCOPE_API_KEY` in the terminal environment. The file uses only Python's standard library, makes all model calls through DashScope (`text-embedding-v4`, `qwen3-rerank`, and `deepseek-v4.1-flash`), and builds an in-memory index. It does not require `DEEPSEEK_API_KEY`, package installation, model downloads, or external data files. See the [exercise instructions](workshops/rag/reranker/README.md).

The course-wide runner invokes this same file in live mode. Without `--live`, it reads a historical snapshot. Other RAG stages retain their existing fixtures; MCP currently uses the shared corpus and a local BGE index.

## MCP, Skills, and Spec-driven development

Start the isolated enterprise fixture in one terminal:

```bash
python workshops/enterprise_context/integration/enterprise_fixture.py
```

Run the task in another terminal:

```bash
python workshops/enterprise_context/harness/run_deepseek.py \
  --out workshops/enterprise_context/runs/flash-001
```

This starts a real stdio MCP client and server, which access a local HTTP fixture. The model discovers Skill names and descriptions, reads instructions and templates, retrieves Jira/Wiki/GitLab context, writes a Spec, modifies the application, and runs independent business checks. The default limit is 24 turns; `--max-turns` accepts 1–40. Use a new output directory for each run.

The fixture contains teaching data, not a production enterprise service. The starting application already works. The task adds project retrieval and subscriptions while preserving existing callers and the shared SDK. The host reruns business checks and records completion claims, Spec files, and actual outcomes separately.

`answer.md` contains the model's explanation; `workspace` contains its edited copy; `summary.json` and `business-check.json` contain independent results. Raw messages and tool results in `events.jsonl` are for local review and are excluded from learner packages.

Check connectivity without model calls:

```bash
python workshops/enterprise_context/integration/client_probe.py \
  --out workshops/enterprise_context/runs/protocol-check
```

## Basic MCP tool calls

```bash
python chapter9/lesson1/mcp_harness.py list-tools
python chapter9/lesson1/mcp_harness.py run \
  --task 'Use calculator to compute sqrt(2) * 100, rounded to two decimal places.'
```

Tool turns preserve complete assistant messages, including `reasoning_content`, before returning tool results to the model. Successful discovery alone does not establish task completion.

## References

- [DeepSeek models and API](https://api-docs.deepseek.com/quick_start/pricing/)
- [Thinking mode and tool messages](https://api-docs.deepseek.com/guides/thinking_mode/)
- [FastEmbed supported models](https://qdrant.github.io/fastembed/examples/Supported_Models/)
