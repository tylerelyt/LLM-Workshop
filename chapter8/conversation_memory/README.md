<a id="lesson-1-managing-conversation-history"></a>

# 对话历史管理

本课学习对话历史管理。通过保留上下文与生成对话摘要，让聊天机器人在连续交互中保持连贯，并控制输入长度。

## 工程任务

客服历史越来越长，缩短窗口节省输入，却可能丢掉回答所需的账户事实。

在 [example1.py](example1.py) 中，固定对话与最后一问，只改变 max_turns 或摘要中的一条事实，每轮只选一项。

结合事实保留情况与输入量，解释你会选择怎样的窗口或摘要策略。

## 学习目标

- **历史管理**：维护对话历史，并将其作为上下文传给大模型。
- **上下文窗口管理**：控制对话历史的长度，使其适应模型的上下文窗口。
- **对话摘要**：压缩较长的对话，保留关键信息，减少传给模型的文本。

---

<a id="file-descriptions"></a>

## 文件说明

- `example1.py`：客服机器人通过滚动历史窗口，为回复保留近期上下文。
- `example2.py`：为较长的对话生成摘要，提取后续交互可以使用的关键信息。
- `requirements.txt`：列出本课所需的 Python 依赖。

---

<a id="setup-and-execution"></a>

## 环境准备与运行

按[模型配置](../../README-DEEPSEEK.md#setup)设置 `OPENAI_BASE_URL`、`OPENAI_MODEL` 和 `OPENAI_API_KEY`，然后从仓库根目录运行。[模型配置](../../README-DEEPSEEK.md#setup)

```bash
python -m pip install -r chapter8/conversation_memory/requirements.txt
python chapter8/conversation_memory/example1.py
python chapter8/conversation_memory/example1.py --max-turns 1
python chapter8/conversation_memory/example1.py --max-turns 0
python chapter8/conversation_memory/example2.py
```

两个脚本使用同一份构造的客服记录和同一个问题“刚才记录的账户号码和余额分别是多少？”。先预测窗口为 `3`、`1`、`0` 时各会发送哪些消息，再运行对照。完整历史包含账号 `123456` 与余额 `$500`，最近一轮只谈验证安排。程序打印实际请求消息，窗口为 `0` 时不应发送先前事实。

窗口按完整的用户／助手消息对选择，回复换行不会占掉额外轮次。历史保存在应用列表中，模型每次只能使用当前请求携带的部分；脚本重启会恢复这份固定教学历史。

再运行 `example2.py`。第一步生成摘要，第二步在新请求中仅带摘要回答相同问题。对照原始记录、打印的摘要和第二次请求，核对账号、余额与尚待验证的事项是否保留。摘要中缺少的事实不能靠同一进程或同一个模型标识找回。

交付三条证据：完整窗口中的正确答案、移除事实后的资料不足、摘要重新携带事实后的答案。每条都附实际发送的消息，并指出答案所依据的内容。先检查传入消息，再评价模型回答，避免把保留的全量应用历史与实际发送的窗口混为一谈。

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

为自己的多轮任务列出必须保留的事实，加入纠正旧信息和长间隔追问，再比较窗口与摘要。跨进程继续任务时，进入[持久记忆](../persistent_memory/README.md)，区分历史裁剪、事实更新和长期保存。

[主题目录](../README.md) · [课程首页](../../README.md)
