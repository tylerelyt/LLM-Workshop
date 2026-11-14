<a id="lesson-4-rlhf-training-data-construction"></a>

# 偏好数据

为同一提示生成两个答案，将它们记录为候选偏好对，再复核排序。偏好数据集为奖励建模和对齐训练提供比较样本。

## 工程任务

两个来源模型回答同一提示，较大的模型或更长的回答不一定更值得偏好。

在 [rlhf_constructor.py](rlhf_constructor.py) 中，固定候选对，只按任务约束复核或交换排序，同时保留来源模型。

固定候选对按事实与任务要求复核排序，记录交换或丢弃的理由，并保留来源。

## 偏好数据字段

| 字段 | 含义 |
|---|---|
| `prompt` | 提供给两个模型的同一输入 |
| `chosen` | 在偏好复核中暂排在前面的答案 |
| `rejected` | 另一个候选答案 |
| `chosen_model`, `rejected_model` | 脚本记录的来源模型 ID |
| `review_status` | 生成时为 `unreviewed`，内容与排序等待复核 |
| `score_chosen`, `score_rejected` | 可在复核时补充的可选分数 |

在人工复核后的数据集中，`chosen` 表示更受偏好的答案，`rejected` 表示偏好较低的答案。本练习先按配置的两个模型 ID 设置初始排序，再由你评估两个答案。

<a id="set-up-the-model-and-run"></a>

## 配置模型并运行

激活课程 Python 环境后，从仓库根目录运行。

```bash
python -m pip install -r chapter5/preference_data/requirements.txt
```

按课程配置导出 `OPENAI_BASE_URL`、`OPENAI_MODEL` 和 `OPENAI_API_KEY`。DeepSeek 示例使用的接口基础地址为 `https://api.deepseek.com`。`--provider openai` 选择 Chat Completions 客户端，本练习的两个模型参数决定实际使用的模型。`--high-model`、`--low-model` 沿用原参数名，分别选择第一个和第二个来源；正确性由后面的复核确定。更换服务接口时，替换对应的模型 ID。[模型配置](../../README-DEEPSEEK.md)

```bash
workshop_out="$(mktemp -d)"
python chapter5/preference_data/rlhf_constructor.py \
  --input-file chapter5/alpaca_data/data/alpaca_demo.jsonl \
  --method model_comparison --provider openai \
  --high-model deepseek-v4-pro --low-model deepseek-flash \
  --max-samples 3 \
  --output-path "$workshop_out/preferences.jsonl"
```

将复核后的Alpaca 数据格式练习输出传给 `--input-file`，即可继续本部分的数据流程。加载器接受 JSON 或 JSONL。处理 Alpaca 记录时，会把 `instruction` 和 `input` 组合为提示。脚本也接受 Few-shot 指令，或直接使用 `prompt` 和 `text` 字段。

使用 DashScope 时，配置 `DASHSCOPE_API_KEY`，指定 `--provider dashscope`，并选择两个可用的 DashScope 模型 ID。

终端默认展示第一条实际候选对的同一提示、两份完整答案和各自模型。`chosen`、`rejected` 是未经人工复核的初始槽位；请依据事实与任务约束判断应保留、交换还是丢弃，长度统计不作为排序依据。


<a id="inspect-the-output"></a>

## 检查输出

先用下面这条故意排错的课堂候选记录练习复核，不需要调用模型。

```json
{
  "prompt": "只回答 23 + 19 的结果。",
  "chosen": "43",
  "rejected": "42",
  "chosen_model": "课堂来源 A",
  "rejected_model": "课堂来源 B",
  "review_status": "unreviewed"
}
```

先独立计算，再按“结果正确且遵守只答数字”这一标准决定排序。将原始记录与修改后的复核版本分别保存，交换答案时一起交换来源模型字段，并在复核版本中记录状态和理由。若两个答案同样满足标准，标记平局并暂不放入二元偏好训练文件。

基础偏好记录包含提示和两个答案。

```json
{
  "prompt": "Please explain what machine learning is",
  "chosen": "Machine learning uses algorithms to learn patterns from data, allowing systems to make predictions or decisions on new examples.",
  "rejected": "Machine learning is a technology that makes machines smart."
}
```

复核者可以按约定的评分标准补充分数。

```json
{
  "prompt": "Please explain what machine learning is",
  "chosen": "Machine learning uses algorithms to learn patterns from data, allowing systems to make predictions or decisions on new examples.",
  "rejected": "Machine learning is a technology that makes machines smart.",
  "score_chosen": 8.5,
  "score_rejected": 3.2
}
```

<a id="construction-and-quality-checks"></a>

## 数据构造与质量检查

`model_comparison` 将同一提示发送给两个模型。`--high-model` 的回答最初放入 `chosen`，`--low-model` 的回答放入 `rejected`。从正确性、完整性和相关性三个方面阅读两个答案，修正排序或标记平局，并记录每项判断的理由。

脚本跳过失败的调用和完全相同的回答。没有剩余候选偏好对时，会报错退出。终端汇总会报告保存的候选对数量、生成成功数量、平均答案长度和长度比。这些是生成完整性与长度统计，利用它们定位需要复核的样本。

检查整个数据集的任务多样性和潜在偏好偏差。留意名义上更强的模型反而给出较弱答案的情况，以及较长回答掩盖事实错误的情况。基于分数的排序和直接人工标注可以补充更多偏好信号。

在线生成后，从相同提示的两份回答中先隐藏模型名称，根据预先写下的正确性、完整性和相关性标准排序，再揭示来源。记录三组复核结果，注明来源模型、决定与理由；平局或证据不足的样本单独保留。将原始生成文件与复核版本一起保存，便于其他复核者追踪改动。

<a id="continue-the-workflow"></a>

## 后续流程

复核后的偏好数据可用于奖励模型训练，以及后续基于 PPO 的 RLHF 流程。用留出的提示评估训练后的模型是否遵循预期偏好。冻结表示与分类头训练见[模型预训练技术基础的迁移学习实验](../../chapter3/frozen_classifier/README.md)

<a id="references"></a>

## 参考资料

- [通过人类反馈训练语言模型遵循指令](https://arxiv.org/abs/2203.02155)
- [Constitutional AI：通过 AI 反馈实现无害性](https://arxiv.org/abs/2212.08073)
- [TRL：Transformer 强化学习](https://github.com/huggingface/trl)

终端默认展示第一条实际候选对的同一提示、两份完整答案和各自模型。`chosen`、`rejected` 是未经人工复核的初始槽位；请依据事实与任务约束判断应保留、交换还是丢弃，长度统计不作为排序依据。

## 在自己的项目中使用

为自己的任务先写正确性与约束标准，再盲评同一输入的候选答案，保留平局和无法判断的样本。若两位复核者意见不一致，回看标准与证据，区分偏好分歧和事实错误；在[反思与改进](../../chapter9/reflection/README.md)中也使用明确依据检查改写。

[主题目录](../README.md) · [课程首页](../../README.md)
