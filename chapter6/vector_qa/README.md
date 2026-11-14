# 轻量向量检索问答

把文档变成能回答问题的系统：先检索原文，再让模型依据原文回答，最后分别核对召回和答案。练习提供构造的合同条款；这些材料用于学习检索机制。

先理解[模型接口与 Session](../../chapter4/model_service/README.md)。你需要分清当前请求中有哪些资料，才能判断回答来自哪里。

## 建立第一个基线

准备 Python 3.11 或 3.12，按[模型配置](../../README-DEEPSEEK.md#setup)设置 Chat Completions 服务。从仓库根目录运行：

```bash
python -m pip install -r chapter6/vector_qa/requirements.txt
export WORKSHOP_LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
export CHROMA_PATH="$(mktemp -d)/chromadb"
python chapter6/vector_qa/vector_qa.py --output /tmp/vector-qa-baseline.json
```

嵌入模型首次运行会下载权重。默认问题是“合同中的主要义务是什么？”。检查实际命中是否包含 `doc2` 的付款、交付和服务条款，再核对回答是否忠实使用这些内容。

只观察检索时加 `--search-only`，不调用聊天服务。`--output` 保存实际原文、距离、回答、引用、语料指纹和耗时；不指定时只打印终端结果。

## 用一组问题判断系统表现

先阅读 [documents.json](data/documents.json) 与 [questions.json](data/questions.json)。问题集包括单条证据、多条证据，以及资料没有提供答案的情况。参考答案由人编写，只用于核对，不会发给模型。

先固定语料、问题集和嵌入来源，只改变 `--top-k`：

```bash
python chapter6/vector_qa/vector_qa.py \
  --cases chapter6/vector_qa/data/questions.json \
  --search-only --top-k 1 --output /tmp/qa-retrieval-k1.json
python chapter6/vector_qa/vector_qa.py \
  --cases chapter6/vector_qa/data/questions.json \
  --search-only --top-k 3 --output /tmp/qa-retrieval-k3.json
```

检查每题 `hits` 与 `review.missing_document_ids`。`reference_evidence_coverage` 是有答案的问题中，完整召回所标参考文档的比例。无答案题不计入这个比例；召回相似资料不能说明资料能回答问题。

接着保持参数不变，去掉 `--search-only` 运行生成：

```bash
python chapter6/vector_qa/vector_qa.py \
  --cases chapter6/vector_qa/data/questions.json \
  --top-k 3 --output /tmp/qa-answers-k3.json
```

逐题比较 `answer`、`hits` 和 `review.reference_answer`，分别判断：

- 所需原文是否进入本轮上下文。
- 答案中的事实是否由引用原文支持，多条证据是否都被使用。
- 资料缺失时是否明确说明，是否编造了手机号或具体签署日期。

`citations_from_current_hits` 只检查引用 ID 是否存在于当前材料，答案质量仍需要人工核对。批量命令正常退出只表示运行完成；生成失败会保留已检索证据并返回非零状态。`generation_calls` 统计逻辑调用，不包含 SDK 内部重试；索引初始化耗时单独记录，逐题耗时包含检索和生成。

## 改一次，解释一次

固定问题与模型，只把 `data/documents.json` 中 `doc2.text` 补上“付款期限为验收后 7 天”，再用 `--question '付款期限是什么？'` 查询。先确认命中原文已更新，再检查回答。语料内容和嵌入来源共同标识索引，修改后不会混入旧版本的残留文档；同一目录会保留独立的旧索引，清理时只删除自己的 `CHROMA_PATH`。

然后恢复教学条款，用相同题集比较 `top-k 1` 与 `top-k 3` 的生成。先预测哪些问题会变化，再看新增证据、无关信息和耗时。证据已完整但答案仍错时，检查提示和生成；所需文档没有召回时，进入[检索与重排](../reranking/README.md)定位候选阶段的问题。

## 从教学语料到自己的文档

选择一个自己能复核的小型文档集合，先整理为 UTF-8 JSON 数组，每份文档给出唯一 ID：

```json
[
  {"id": "release", "text": "常规发布必须完成审批与回归测试。"},
  {"id": "rollback", "text": "紧急回滚由当班负责人批准。"}
]
```

在运行前写出参考问题，注明需要哪些文档和什么样的答案。不能回答的问题使用空文档列表，并标注 `expected_abstention: true`：

```json
[
  {
    "id": "approval",
    "question": "紧急回滚由谁批准？",
    "expected_document_ids": ["rollback"],
    "expected_abstention": false,
    "reference_answer": "当班负责人，引用 rollback 中的审批规则。"
  },
  {
    "id": "phone",
    "question": "当班负责人的手机号是什么？",
    "expected_document_ids": [],
    "expected_abstention": true,
    "reference_answer": "文档未提供手机号，应说明资料不足。"
  }
]
```

将两份文件分别保存为 `/tmp/my-documents.json` 和 `/tmp/my-questions.json` 后运行：

```bash
python chapter6/vector_qa/vector_qa.py \
  --documents /tmp/my-documents.json --cases /tmp/my-questions.json \
  --top-k 1 --output /tmp/my-qa-baseline.json
```

脚本会检查重复 ID、空正文、无效参考文档和相互矛盾的标注，在加载模型前拒绝无效输入。数据格式检查完成后，仍由你复核参考答案是否正确。

先用开发题集定位问题和修改方案，再用一组未参与调整的问题复核。结果中保留语料与题集指纹，比较时确认输入一致；修改语料后重新审阅参考标注。候选召回只是评估的一部分，新增正确问题和仍然失败的问题都要逐条查看。

当文档解析和分块成为瓶颈，继续看[文档提取](../document_qa/README.md)与[切块反馈](../chunk_feedback/README.md)。需要将查询暴露为 Agent 工具时，参考[检索服务接入 Harness](../../chapter9/rag_mcp/README.md)；该练习使用另一套带版本的教学语料，需要按其结构适配数据。

[主题目录](../README.md) · [系统实践](../../README.md#系统实践)
