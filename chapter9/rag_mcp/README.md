# 检索服务接入 Harness

团队已有向量检索，但开发人员要切到另一个界面才能查规范。请把知识库的检索能力接进大家日常使用的 Harness。使用场景是紧急回滚：支付网关的审批人刚刚变更，有人会在同一会话里重问。你的实现必须能说明答案来自哪一版原文，以及什么时候证据不够。

## 工程任务

审批人已经更新，Agent 却可能沿用会话中的旧答案。

在 [__main__.py](__main__.py) 中，固定模型、问题和检索设置，只更新语料副本中的审批条款及版本。

用本轮工具返回的版本和引用证明是否重新检索，决定怎样处理旧事实与缺少证据的追问。

## 学员要完成的工作

- 沿用已有的分块、BGE 向量索引和召回。为检索设计一个只读 MCP Tool。输入限制在查询和候选数量，返回可回查的原文、出处、片段标识与版本。回答由 Harness 根据工具观察生成。
- 在自己的 Harness 中注册 MCP Server。发起一条业务问题，留下工具发现、调用参数、原文结果及最终引用。说明为什么此处用 Tool 支持模型主动搜索。
- 更新教学语料中的支付回滚条款。在同一个 Harness 会话重问，比较两次命中的条款版本和审批人。再问语料未提供的审批人手机号，检查模型如何处理证据不足。

保留工具定义、Harness 配置和三次查询的轨迹。验收以实际 MCP 响应和引用为准。需要同时看到旧版与新版的正确结论、引用与返回原文一致，以及缺少证据时不输出臆测值。语料位于 [共同语料 documents.json](../../chapter6/shared/rag/documents.json)。可在阅读参考实现前独立完成，也可以在参考实现上修改检索策略。

## 运行参考实现

先修：[检索与重排](../../chapter6/reranking/README.md)和[MCP 基础](../mcp_tools/README.md)。本练习独立核对工具发现、语料更新与最终引用。

在仓库根目录安装现有课程依赖。BGE 模型初次运行会下载，已有缓存可用 `FASTEMBED_CACHE_PATH` 指定。

```bash
python -m pip install -r requirements-deepseek.txt
python -m chapter9.rag_mcp --output chapter9/rag_mcp/results/protocol.json
python -m chapter9.rag_mcp --live --output chapter9/rag_mcp/results/mcp-live.json
```

默认终端显示本轮问题、关键证据与结果对照；指定 `--output` 后仍显示课堂摘要，完整轨迹写入文件。需要在终端查看完整结构时加 `--json`；离线回放、模型调用与协议验证的范围会在输出中区分。


第一条运行命令走真实 stdio MCP，核对工具发现、候选数量、参数校验和同一连接内的语料刷新。加上 `--live` 后，参考 Harness 使用课程配置的模型决定何时调用工具，并把真实 MCP 响应交给模型继续作答。密钥按 [课程配置](../../README-DEEPSEEK.md) 在本机设置。程序只更新临时语料副本。

先在 `protocol.json` 中查看 `tool_schema`、`before` 和 `after`，核对片段原文与 `payment-rollback` 的版本从 1 变成 2。`checks.rejects_invalid_top_k` 来自一次实际的非法参数调用，`answers` 在该模式下为空。这里验证本地教学检索服务的协议和索引刷新。

再打开 `mcp-live.json` 中的 `answers`。每条记录保留 `observations` 和 `response`，逐条核对模型实际传入的 `query`、`top_k`、返回的 `citation_id` 与最终引用。三次查询分别应支持“发布负责人”、更新后的“当班 SRE”，以及手机号“资料不足”的结论。在线模型的调用记录才能证明模型使用了本轮工具观察。

受控修改只发生在自己的语料副本：固定问题和检索设置，更新审批人以及 `metadata.version`，在同一个会话中重问。检查器和证据原文不作为绕过失败的修改项。参考命令每次新建并清理临时副本；自己的 Harness 使用下方 `CORPUS`，重做时创建新副本，保留两轮报告便于核对。

## 接入你自己的 Harness

以 Claude Code 的 stdio 接入为例。在仓库根目录运行下列命令，使用已安装课程依赖的 Python。其他支持 stdio MCP 的 Harness 使用同一条服务启动命令。

```bash
PYTHON="$(python -c 'import sys; print(sys.executable)')"
CORPUS="$(mktemp -d)/corpus.json"
cp chapter6/shared/rag/documents.json "$CORPUS"
claude mcp add --transport stdio --scope local rag-knowledge -- \
  "$PYTHON" -m chapter9.rag_mcp.server --corpus "$CORPUS"
claude mcp list
```

进入会话后通过 `/mcp` 查看工具，要求先调用 `search_knowledge`，再带出处、版本和引用回答。手动修改副本时，同时更新条款正文和 `metadata.version`，保存后重新提问。若从其他目录启动 Harness，将服务的工作目录设为仓库根目录，或在 MCP 进程环境中配置仓库根目录为 `PYTHONPATH`。

[Claude Code MCP 接入文档](https://code.claude.com/docs/en/mcp) · [MCP Tools 规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)


## 在自己的项目中使用

把自己的文档检索包装成只读工具，保留来源、版本和原文，再用[固定问题集](../../chapter6/vector_qa/README.md#从教学语料到自己的文档)核对回答。加入原文更新和未知信息的追问，检查 Agent 是否重新取证；需要管理整个循环时，继续看[MCP Harness](../mcp_harness/README.md)。

[主题目录](../README.md) · [课程首页](../../README.md)
