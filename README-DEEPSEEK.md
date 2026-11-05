# 用 DeepSeek Flash 运行企业级智能体课程练习

这份适配覆盖本课程使用的 RAG、MCP、Skill 与 Spec 研发练习。所有生成与工具调用统一使用 DeepSeek 官方接口；密钥通过本机环境变量读取。其他章节的独立示例仍可从各自目录运行。

## 准备环境

在仓库根目录执行，使用 Python 3.11 或 3.12：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-deepseek.lock
cp .env.example .env
```

在 `.env` 中填写 `DEEPSEEK_API_KEY`。该文件已被 Git 忽略。也可以保留密钥在仓库外，再用 `DEEPSEEK_ENV_FILE` 指向它；不要把实际密钥放进命令示例或学员包。

默认模型名为 `deepseek-flash`。截至 2026 年 11 月 1 日，官方说明该名称对应 DeepSeek V4.1 Flash，旧的 `deepseek-v4-flash` 也会转到这一模型。可用 `DEEPSEEK_MODEL` 更换调用名。接口地址默认 `https://api.deepseek.com`。

## 第一部分：带 Reranker 的 RAG

本章的 [RAG 工程练习](workshops/rag/README.md) 可独立运行，包含重排、去重、反馈打标、分语种检索、图谱迭代和 MCP 接入。

```bash
python -m workshops.rag all --output workshops/rag/results/offline.json
python -m workshops.rag all --live --output workshops/rag/results/live.json
python -m workshops.rag reranker --live
python -m workshops.rag mcp --live
```

其中 MCP 环节的离线模式也会使用真实 BGE 索引与 stdio 连接，需要课程依赖和模型缓存。重排离线结果是此前 8 篇文档的快照。重排真实运行与 MCP 共用 `workshops/rag/documents.json`，包含来源、版本和支付回滚条款。

第一次运行会下载约 90 MB 的中文 BGE-small ONNX 嵌入模型。文档经过分块和嵌入后，向量与原文保存到 `workshops/rag/results/index`；后续相同语料和模型复用索引。提问时再生成查询向量、召回候选、重排候选，最后分别用“直接召回”和“加入重排”的上下文生成答案。

这条轻量路线用 **BGE-small 做向量召回、DeepSeek Flash 做相关性重排和回答**，没有把 LLM 重排称为 BGE Cross-Encoder。BGE-m3 + BGE-reranker 路线位于 `chapter3/lesson1/rag_pipeline.py`，其生成器也已改为 DeepSeek；需要单独安装该目录的 `requirements.txt`。

统一入口的结果保存在 `--output` 指定的位置。逐题调参入口的结果保存在 `workshops/rag/results/run.json`，包括候选、分数、引用、文档级证据召回率、倒数排名、耗时和真实 API usage。逐题入口中，五道题启用生成时默认调用模型 15 次；不加 `--generate` 时只做检索与模型重排，仍会调用 Flash。

可以只运行一个问题，或改变候选量和最终入选量：

```bash
python chapter3/lesson1/deepseek_workshop.py --generate --retrieve 8 --keep 3 \
  --question '页面正文没有变化，但迁到了另一个项目，订阅方应该收到什么通知？'
```

## 第二、三部分：MCP、Skill 与 Spec 研发

在第一个终端启动隔离企业服务：

```bash
python workshops/enterprise_context/integration/enterprise_fixture.py
```

在第二个终端启动 Flash 的完整任务：

```bash
python workshops/enterprise_context/harness/run_deepseek.py \
  --out workshops/enterprise_context/runs/flash-001
```

这个入口启动真实的 stdio MCP 客户端与服务端，MCP 再访问本机 HTTP 企业演示接口。模型先看到 Skill 名称与简介，再自行读取正文和模板；随后读取 Jira、Wiki、GitLab，编写 Spec、修改应用并运行独立业务检查。默认最多 24 个模型回合，可通过 `--max-turns` 调整到 1—40；输出目录每次必须新建，以便保留原运行。

本机 HTTP 服务是课程构造的数据，不是线上企业系统。起始应用已经可以运行；任务是在保留既有调用和共享 SDK 的前提下增加项目检索与订阅。宿主最后会再次执行业务检查，完成声明、Spec 文件和业务结果分别记录。

结果位于指定目录：`answer.md` 是模型说明，`workspace` 是模型实际修改的工作副本，`summary.json` 和 `business-check.json` 是独立检查结果。`events.jsonl` 保留原始模型消息及工具返回，仅供本机复核，不随学员包分发。

若需要先检查协议连通性、不调用模型：

```bash
python workshops/enterprise_context/integration/client_probe.py \
  --out workshops/enterprise_context/runs/protocol-check
```

## 基础 MCP 调用示例

```bash
python chapter9/lesson1/mcp_harness.py list-tools
python chapter9/lesson1/mcp_harness.py run \
  --task '调用 calculator 计算 sqrt(2) * 100，保留两位小数。'
```

工具回合会保留完整的 assistant 消息，包括 `reasoning_content`，再把工具结果交回模型。没有只把最终正文拼回请求，也没有把工具发现成功当作任务完成。

## 核对依据

- [DeepSeek 模型名与接口](https://api-docs.deepseek.com/quick_start/pricing/)
- [思考模式与工具调用消息回传](https://api-docs.deepseek.com/guides/thinking_mode/)
- [FastEmbed 支持的嵌入模型](https://qdrant.github.io/fastembed/examples/Supported_Models/)

本次实际运行和仍未运行的范围，见课程交付入口中的核验记录。
