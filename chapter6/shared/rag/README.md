# RAG 共享数据与批量运行器

教学练习分别位于[提示与检索练习](../../README.md)的独立课时中。本目录维护共同语料、索引组件及批量复核入口。

```bash
python -m chapter6.shared.rag all --output chapter6/shared/rag/results/offline.json
python -m chapter6.shared.rag all --live --output chapter6/shared/rag/results/live.json
```

`all` 仅用于批量检查。单项运行入口：重排使用 `python -m chapter6.shared.rag reranker`，去重/质量/语言/图检索分别使用 `python -m chapter6.semantic_dedup`、`python -m chapter6.chunk_feedback`、`python -m chapter6.cross_language` 与 `python -m chapter6.graph_search`，检索 MCP 使用 `python -m chapter9.rag_mcp`。在线模式的模型配置见[配置指南](../../../README-DEEPSEEK.md)。

各练习的离线含义不同。重排读取历史快照，其 `result.usage` 是原记录，本次 `api_calls` 为 0。去重使用固定判定，质量练习分析反馈回放，跨语言练习使用固定译文，图检索使用脚本策略。MCP 练习则执行真实 stdio 协议和本地 BGE 检索，模型文件与依赖仍须准备好；它的 `answers` 在未加 `--live` 时为空。

`--live` 会为所选练习调用在线模型。第一项仍需 DashScope 嵌入与重排权限，其余模型配置沿用课程聊天接口。查看每项 `result` 中的原文、轨迹和检查项，再判断是否达到题面要求。固定数据和脚本模型验证支持复现程序路径，在线模型的质量结论需另看本轮调用与回答。

[共同语料](documents.json) · [评估问题](questions.json)
