# Workshop：把 RAG 封装成 MCP，接进自己的 Harness

团队已有向量检索，但开发人员要切到另一个界面才能查规范。请把知识库的检索能力接进大家日常使用的 Harness。使用场景是紧急回滚：支付网关的审批人刚刚变更，有人会在同一会话里重问。你的实现必须能说明答案来自哪一版原文，以及什么时候证据不够。

## 学员要完成的工作

- 沿用已有的分块、BGE 向量索引和召回。为检索设计一个只读 MCP Tool。输入限制在查询和候选数量，返回可回查的原文、出处、片段标识与版本。回答由 Harness 根据工具观察生成。
- 在自己的 Harness 中注册 MCP Server。发起一条业务问题，留下工具发现、调用参数、原文结果及最终引用。说明为什么此处用 Tool 支持模型主动搜索。
- 更新教学语料中的支付回滚条款。在同一个 Harness 会话重问，比较两次命中的条款版本和审批人。再问语料未提供的审批人手机号，检查模型如何处理证据不足。

提交工具定义、Harness 配置和三次查询的轨迹。验收以实际 MCP 响应和引用为准。需要同时看到旧版与新版的正确结论、引用与返回原文一致，以及缺少证据时不输出臆测值。语料位于 [共同语料 documents.json](../documents.json)。可在阅读参考实现前独立完成，也可以在参考实现上修改检索策略。

## 运行参考实现

在仓库根目录安装现有课程依赖。BGE 模型初次运行会下载，已有缓存可用 `FASTEMBED_CACHE_PATH` 指定。

```bash
python -m pip install -r requirements-deepseek.txt
python -m workshops.rag mcp
python -m workshops.rag mcp --live --output workshops/rag/results/mcp-live.json
```

第一条运行命令走真实 stdio MCP，核对工具发现、候选数量、参数校验和同一连接内的语料刷新。加上 `--live` 后，参考 Harness 使用 `deepseek-flash` 决定何时调用工具，并把真实 MCP 响应交给模型继续作答。密钥按 [课程配置](../../../README-DEEPSEEK.md) 在本机设置。程序只更新临时语料副本。

## 接入你自己的 Harness

以 Claude Code 的 stdio 接入为例。在仓库根目录运行下列命令，使用已安装课程依赖的 Python。其他支持 stdio MCP 的 Harness 使用同一条服务启动命令。

```bash
PYTHON="$(python -c 'import sys; print(sys.executable)')"
CORPUS="$(mktemp -d)/corpus.json"
cp workshops/rag/documents.json "$CORPUS"
claude mcp add --transport stdio --scope local rag-knowledge -- \
  "$PYTHON" -m workshops.rag.mcp_harness.server --corpus "$CORPUS"
claude mcp list
```

进入会话后通过 `/mcp` 查看工具，要求先调用 `search_knowledge`，再带出处、版本和引用回答。手动修改副本时，同时更新条款正文和 `metadata.version`，保存后重新提问。若从其他目录启动 Harness，将服务的工作目录设为仓库根目录，或在 MCP 进程环境中配置仓库根目录为 `PYTHONPATH`。

[Claude Code MCP 接入文档](https://code.claude.com/docs/en/mcp) · [MCP Tools 规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
