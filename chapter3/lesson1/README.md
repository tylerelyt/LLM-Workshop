# 两阶段 RAG：向量召回、重排与答案生成

本课程的默认入口使用中文 BGE-small 嵌入、DeepSeek Flash 重排与生成，适合在普通开发机上完成整个实验。安装和密钥配置见仓库根目录的 [DeepSeek 运行说明](../../README-DEEPSEEK.md)。

从仓库根目录运行：

```bash
python -m workshops.rag reranker
python -m workshops.rag reranker --live
python -m workshops.rag all --live
```

文档入库时分块、嵌入并保存向量；查询时生成查询向量、召回候选、由 Flash 重排，再分别生成两组可对照的答案。结果包含引用、相关文档召回率和真实 API usage。

BGE-m3 + BGE-reranker 实现位于 `rag_pipeline.py`，生成服务已改成 DeepSeek。若使用这条路线，另行安装本目录的 `requirements.txt`。该实现只使用 BGE-m3 的稠密向量，不声称启用了稀疏检索或 ColBERT。检索相关性也不再被当作答案正确率。

Flash 的 LLM 重排与 BGE Cross-Encoder 是两种不同实现；实验报告分别标明。课程材料与题目共用 `workshops/rag`，没有复制出另一套题目。

沿着同一套 RAG 继续完成去重、反馈、语种分库、图谱迭代与 MCP 接入，见 [完整题面与运行说明](../../workshops/rag/README.md)。逐题调整召回量、最终入选量和问题，可继续运行 `python chapter3/lesson1/deepseek_workshop.py --generate`。
