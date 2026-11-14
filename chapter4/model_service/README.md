<a id="lesson-1-getting-started-with-open-source-llms"></a>

# 标记化、模型服务与无状态推理

先用一个聊天服务观察请求、Token 用量与对话历史，再用本地模型观察文本续写和 Chat 模板。两种运行方式分别准备，不需要先下载本地权重才能调用 API。

<a id="setup-and-execution"></a>

## 先运行 Session 实验

客服刚确认过工单号，下一次请求却可能回答不知道。本实验向同一模型发送三组消息，检查事实是否真的进入当前输入。

准备 Python 3.11 或 3.12，按[模型配置](../../README-DEEPSEEK.md#setup)填写 `OPENAI_BASE_URL`、`OPENAI_MODEL` 和 `OPENAI_API_KEY`。从仓库根目录运行：

```bash
python -m pip install 'openai>=2,<3'
python chapter4/model_service/maas_session.py --output /tmp/session-baseline.json
```

每次运行发起三次 Chat Completions 请求。依次查看终端打印的服务地址、模型、消息、回答和用量：

| 请求 | 应用发送了什么 | 要检查什么 |
| --- | --- | --- |
| A | 告知本次工单号 | 模型怎样回答，应用保存了哪些消息 |
| B | 在独立消息列表中直接询问工单号 | 输入没有事实时，是否按指令回答“资料不足” |
| C | 回传 A 的消息，再问相同问题 | 工单号来自本轮输入的哪条消息 |

`maas_session.py` 中的 `saved` 与 `independent` 是程序维护的消息列表，每次请求都显式传给服务。Session 在应用侧保存状态，重启脚本会重新建立这些列表。服务端推理缓存与这份对话历史承担不同职责。

`--output` 保存实际消息快照、回答、服务报告的 Token 用量与每次请求耗时。程序还核对 B 是否拒绝猜测、C 是否使用当前工单号；检查失败会返回非零状态。这项检查只针对本例事实，不能替代其他任务的质量评估。

## 改变工单号，检查信息来自哪里

保持模型和追问不变，只改变本次事实：

```bash
python chapter4/model_service/maas_session.py \
  --reference WS-9102 --output /tmp/session-new-reference.json
```

运行前先预测 B、C 的回答，再对照两次请求。检查 C 是否使用新的工单号，B 是否仍说明资料不足。沿 [ask](maas_session.py) 找到历史写入和请求发送的位置，说明状态由谁保存。

## 观察 Token、续写与 Chat 输入

这组实验加载本地权重，需要额外依赖和模型下载。使用 `WORKSHOP_LOCAL_MODEL` 选择模型，下面沿用一个较小的指令模型：

```bash
python -m pip install -r chapter4/model_service/requirements.txt
cd chapter4/model_service
export WORKSHOP_LOCAL_MODEL=Qwen/Qwen2.5-0.5B-Instruct
python example1.py --max-new-tokens 8
python example1.py --max-new-tokens 32
python example2.py
```

首次运行会下载权重。[模型资料](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)说明其训练与使用方式。

- `example1.py` 将原始文本作为续写起点。对照两次运行的输入 Token、前 12 个片段、输出 Token 数与停止情况，理解逐 Token 预测（NTP）和输出预算。
- `example2.py` 打印角色消息及聊天模板转换后的文本，再生成中文诗歌。比较 Chat 消息怎样被组织为模型输入。

一个 Token 可以是字、词的一部分或标点。输出未用满预算时，检查是否已生成结束标记。模型是否经过指令或对话训练会影响适用任务，输入包装本身不会更新模型权重；MaaS 是否同时提供传统 Completion 接口，需要看服务自身支持的能力。

<a id="next-steps"></a>

## 用到自己的应用

换成自己的一条业务事实，画出它在用户输入、应用存储和模型请求之间的流转。接着在[向量问答](../../chapter6/vector_qa/README.md)中找到原文进入输入的位置，或在[对话历史](../../chapter8/conversation_memory/README.md)中观察窗口裁剪与摘要怎样影响事实保留。

<a id="file-descriptions"></a>

<details>
<summary>其他示例：本地历史、检索与 Flask 多服务</summary>

以下程序各自展示不同的调用方式。在 `chapter4/model_service` 目录、同一套本地模型配置下运行：

```bash
python example3.py
python example4.py
```

`example3.py` 从输入历史找回订单号，修改首条消息中的 `12345` 后重跑，检查它是否跟随新事实。`example4.py` 在没有配置 Google Custom Search 时使用固定教学片段；真实检索路径及服务要求见该脚本的参数和[模型配置](../../README-DEEPSEEK.md)。

Flask 示例使用独立的专家服务与协调者，配置同一份 `OPENAI_*` 变量后，在三个终端从本目录分别启动：

```bash
python agent_a.py
```

```bash
python agent_b.py
```

```bash
python agent_c.py
```

保持服务运行，再向协调者发送请求：

```bash
curl http://127.0.0.1:5002/integrate \
  -H 'Content-Type: application/json' \
  -d '{"task":"先调用 ai_expert 询问 AI 助教收集哪些字段，再调用 law_expert 询问隐私告知，最后汇总两方建议。"}'
```

查看专家服务是否真的收到请求，再核对协调者的回答。端口由 `WORKSHOP_AI_PORT`、`WORKSHOP_LAW_PORT` 和 `WORKSHOP_COORDINATOR_PORT` 设置；在三个终端中保持一致。

这组服务使用 `common.py` 提供的公共函数，与前面的 Session 实验独立运行。

</details>

[主题目录](../README.md) · [全部练习](../../README.md#练习索引)
