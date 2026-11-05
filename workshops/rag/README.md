# 把 RAG 从检索做成团队可用的知识服务

先把文档分块、投影和入库，完成候选召回、重排与答案生成。接着围绕这套流程处理实际使用中出现的问题，最后让大家在自己的 Harness 中直接查询知识库。

| 环节 | 要完成的工作 | 题面 |
|---|---|---|
| 召回与重排 | 固定候选和上下文名额，比较证据覆盖与答案引用 | [两阶段检索](reranker/README.md) |
| 索引维护 | 在线发现相似片段，离线判断合并，保留版本与归档 | [语义去重](dedup/README.md) |
| 反馈回流 | 识别片段质量与查询相关性的区别，整理维护记录和对齐样例 | [质量打标](quality/README.md) |
| 跨语种查询 | 分语种建立索引，翻译查询并比较漏召回是否改善 | [语种分库](language/README.md) |
| 渐进式获取 | 根据已观察到的关系继续探索，逐步补足所需知识 | [图谱迭代检索](graph/README.md) |
| 日常工具接入 | 用 MCP 发布同一套 BGE 检索，在 Harness 中核对引用和版本变化 | [接入 Harness](mcp_harness/README.md) |

## 运行课程

环境和密钥配置见 [DeepSeek 运行说明](../../README-DEEPSEEK.md)。在仓库根目录执行。

```bash
python -m workshops.rag all --output workshops/rag/results/offline.json
python -m workshops.rag all --live --output workshops/rag/results/live.json
python -m workshops.rag reranker --live
python -m workshops.rag mcp --live
```

将 `all` 换成 `reranker`、`dedup`、`quality`、`language`、`graph` 或 `mcp`，即可单独完成对应环节。真实模式统一使用 DeepSeek Flash。重排与 MCP 复用中文 BGE-small 和 [documents.json](documents.json)，文档的 `metadata` 保存来源和版本。索引在语料或模型改变后重建。MCP 版本更新实验只修改临时副本。

离线模式中，重排读取此前真实运行的快照，去重、反馈、语种和图谱使用明确标注的教学预演。MCP 仍会建立真实 stdio 连接和 BGE 索引，需要安装课程依赖及准备嵌入模型缓存。`FASTEMBED_CACHE_PATH` 可指定缓存位置，`HF_HUB_OFFLINE=1` 可强制只读取本地模型。

去重与语种练习使用轻量相似度替身，重点核对维护决策和查询适配。图谱使用隔离数据。迁入生产知识库时，应换成项目实际使用的存储、投影模型和图谱，并用本项目问题集重新验证。

## 查看每个检索阶段

保留逐题调参入口，便于在课程中检查候选量、最终入选量和问题变化。

```bash
python workshops/rag/deepseek_workshop.py --check-data
python workshops/rag/deepseek_workshop.py --generate --retrieve 8 --keep 3
```

`results/index` 保存向量和原文，运行结果保存候选、引用、排名、耗时和真实 usage。索引适合教学小语料。若选用 BGE-m3 与 BGE-reranker，安装 `requirements-bge.txt` 后运行 `workshop.py --generate`。两条路线均使用共同语料，模型名称与评分方法随结果记录。
