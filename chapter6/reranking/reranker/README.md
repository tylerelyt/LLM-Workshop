<a id="exercise-1-build-a-two-stage-rag-pipeline"></a>

# 练习一：构建两阶段 RAG 流程

打开[lab.py](lab.py)，按顺序执行其中的 `# %%` 单元。样例文档、API 调用、建立索引、召回、重排、组装提示和生成答案都放在同一个独立文件里。运行只需 Python 标准库，脚本自带样例数据，通过远程服务调用模型。

<a id="run"></a>

## 运行

在终端环境变量中设置 `DASHSCOPE_API_KEY`，然后运行：

```bash
python chapter6/reranking/reranker/lab.py
```

在 VS Code 中，用 **Run Cell（运行单元）** 或 **Run Above（运行以上单元）** 查看中间结果。脚本复制到仓库外也能独立运行。执行调用模型 API 的单元会产生用量费用。

需要更换回答模型时，按[模型配置说明](../../../README-DEEPSEEK.md)导出 `OPENAI_BASE_URL`、`OPENAI_MODEL` 和 `OPENAI_API_KEY`。向量化与重排仍使用 DashScope 凭据。

<a id="cells"></a>

## 单元

1. 配置三个 DashScope 模型和问题，查看合成教学文档。
2. 文档分块并生成向量，将向量和原文片段一同保留在内存中。
3. 将问题向量化，用余弦相似度召回候选片段。
4. 使用专用重排模型重新排序，查看入选片段。
5. 把片段填入 `{retrieved_context}`，把问题填入 `{question}`，查看完整提示。
6. 生成并显示答案，查看 `RESULT` 与 `USAGE`。

实验默认使用 DashScope 的 `text-embedding-v4`、`qwen3-rerank` 和 `deepseek-v4.1-flash`。修改 `QUESTION`、`RETRIEVE_K` 或 `KEEP_K`，再从对应单元重新执行。每次执行建立索引的单元都会重建内存索引。重排分数与余弦相似度含义不同，应分别查看各自的排序结果。

核对答案是否得到入选片段支持，显示的出处是否正确。脚本展示模型答案，事实正确性由学员结合原文复核。

课程统一运行器通过 `python -m chapter6.shared.rag reranker --live` 调用同一个文件。省略 `--live` 时，运行器读取历史快照。

<a id="read-the-execution-log"></a>

## 阅读运行日志

输出按六个编号阶段组织，每行附带已用时间。每次 API 请求都会记录模型、开始、完成、耗时与 Token 用量。建立索引时显示原文片段和向量前五项。召回阶段显示候选名次与余弦相似度，重排阶段显示排序变化和被排除的片段。组装提示时打印空模板及实际填充后的完整提示，最后展示答案和各模型用量汇总。日志省略凭据与完整向量数组。

需要同时显示并保存本次运行时，执行：

```bash
mkdir -p chapter6/shared/rag/results
python -u chapter6/reranking/reranker/lab.py | tee chapter6/shared/rag/results/execution.log
```

日志包含样例原文、问题、提示与答案。若把教学数据替换为私有资料，应按相同的数据访问要求管理生成的日志。
