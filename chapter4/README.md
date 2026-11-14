# 预训练语言模型基础

理解模型每次接收什么、怎样生成，以及应用怎样使用 MaaS 提供的能力。

## 从一次请求开始

进入[模型接口、Token 与 Session](model_service/README.md)，依次观察：

- 标记化怎样把输入变成 Token，NTP 怎样把生成组织为逐 Token 预测。
- Completion 与 Chat 接口怎样表达任务，服务怎样接收请求并返回输出、用量和停止原因。
- 请求上下文与输出预算怎样约束生成。
- 不携带历史和显式携带历史的请求有什么区别，Session 的状态由谁维护。

先比较实际消息与回答，再阅读对应原理。用相同问题改变一项输入条件，解释差异来自消息、预算还是服务行为。

## 把理解带入系统

为自己的应用画出一次请求：资料从哪里进入、历史存在哪里、哪些信息需要随下一次请求发送。把这份图带入[文档问答](../chapter6/vector_qa/README.md)，观察检索原文怎样加入输入；再看[对话历史管理](../chapter8/conversation_memory/README.md)，研究上下文增长后的取舍。

结合专栏继续学习标记化、自监督、RNN、注意力与 Transformer，理解接口背后的模型机制。

## 参考阅读

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)：结合专栏理解自注意力、位置编码与 Transformer 结构。
- [BERT：深度双向 Transformer 预训练](https://arxiv.org/abs/1810.04805)：对照自回归生成，理解不同预训练目标与上下文使用方式。
- [语言模型是无监督多任务学习器](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)：理解语言建模目标怎样承载多种任务，并回到实验检查任务文本怎样进入输入。
- [PagedAttention：大语言模型服务的高效内存管理](https://arxiv.org/abs/2309.06180)：理解服务端 KV Cache 管理，与应用保存的 Session 历史区分开来。
- [FlashAttention-2](https://arxiv.org/abs/2307.08691)：从注意力计算的并行与内存访问理解推理基础设施的优化层次。

[学习地图](../README.md#学习地图) · [模型配置](../README-DEEPSEEK.md#setup)
