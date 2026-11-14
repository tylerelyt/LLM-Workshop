<a id="lesson-2-self-instruct-data-construction"></a>

# Self-Instruct 数据

从少量种子任务生成新指令及输入输出实例。用一条记录追踪“指令 → 分类判定 → 原始实例 → 过滤决定”，解释基础规则为什么保留或丢弃它，再判断答案内容是否可用。

## 工程任务

自动生成的指令数据可能格式正确、内容却不可用。

在 [self_instruct_workshop.py](self_instruct_workshop.py) 中，固定种子任务、生成模型与参数，只改变一条过滤规则。

固定同一批生成记录检查过滤决定，再用人工标准判断答案是否正确、任务是否有覆盖。

## Self-Instruct 工作流程

1. 加载覆盖多种工作类型的种子任务。
2. 让模型生成更多指令。
3. 识别分类任务，并生成适用的输入输出实例。
4. 应用质量过滤条件，按指令和输入去重。

生成的 JSONL 使用 `instruction`、`input` 和 `output` 字段，可与 Alpaca 格式的记录进入相同的数据复核和监督微调流程。

<a id="set-up-the-model"></a>

## 配置模型

激活课程 Python 环境后，从仓库根目录运行。

```bash
python -m pip install -r chapter5/self_instruct/requirements.txt
```

为所选 Chat Completions 服务导出 `OPENAI_BASE_URL`、`OPENAI_MODEL` 和 `OPENAI_API_KEY`。使用 DeepSeek 时，接口基础地址设为 `https://api.deepseek.com`，模型设为 `deepseek-flash`。密钥保存在终端环境中，共用设置见课程说明。[模型配置](../../README-DEEPSEEK.md)

脚本也支持 DashScope。只配置 `DASHSCOPE_API_KEY` 时，会选择该服务及其默认模型。

<a id="run-the-exercise"></a>

## 运行练习

```bash
workshop_out="$(mktemp -d)"
SELF_INSTRUCT_OUTPUT="$workshop_out" \
  python chapter5/self_instruct/self_instruct_workshop.py
```

指令扩展最多尝试三次，失败或重复输出不足时会停止并报错。分类识别调用失败或未返回 Yes/No 时也会停止，先修正环境或模型响应后重跑。脚本按自身所在目录加载自带的 `data/seed_tasks.jsonl`，默认生成五条候选指令。内置的备用种子任务涵盖学习计划、数据结构、测试用例、摘要和 SQL。

| 输出文件 | 检查内容 |
|---|---|
| `step1_instructions.jsonl` | 新生成的指令及其多样性 |
| `step2_is_classification.jsonl` | 每条指令是否被视为分类任务 |
| `step3_raw_instances.jsonl` | 过滤前生成的输入和答案 |
| `step4_final.jsonl` | 通过基础规则、仍待复核的记录 |
| `step4_filter_report.jsonl` | 每条原始记录的保留/拒绝决定与规则原因 |

同时打开原始实例文件与最终实例文件。选一条记录解释其保留原因，再检查被过滤记录的原因。最终文件应至少包含一条通过规则的候选示例。没有候选示例时，程序会报错退出，并提示检查原始实例。

终端按步骤展示同一条指令的分类判定、实际输入输出，以及保留和过滤各一条样本及原因；本轮不存在某类样本时会明确说明。过滤说明与实际过滤共用判断结果，不会为了演示补造被拒样本。


## 先验证过滤规则

下面使用四条课堂构造记录，直接调用同一个 `step4_filter_and_dedupe`。它不调用模型，先让你预测规则会保留哪些记录。

```bash
python - <<'PY_LOCAL'
import tempfile
from chapter5.self_instruct.self_instruct_workshop import step4_filter_and_dedupe
records = [
    {"instruction": "判断评论的情感", "input": "服务很好", "output": "正面"},
    {"instruction": "判断评论的情感", "input": "服务很好", "output": "正面"},
    {"instruction": "判断评论的情感", "input": "服务很差", "output": ""},
    {"instruction": "判断评论的情感", "input": "非常满意", "output": "负面"},
]
out_dir = tempfile.mkdtemp()
kept = step4_filter_and_dedupe(records, out_dir)
print("保留数量", len(kept), "结果目录", out_dir)
PY_LOCAL
```

打开该目录的报告，核对重复记录和空答案各自的拒绝原因。再读保留下来的两条内容，指出其中的标签错误。将空答案补为正确标签，其他条件不变重跑，检查保留数量的变化。这让你区分规则过滤覆盖了什么，以及人工内容复核还需要发现什么。

<a id="output-examples"></a>

## 输出示例

```json
{"instruction": "Explain the properties of a binary search tree and give an example", "input": "", "output": "..."}
{"instruction": "Write an SQL query based on the requirement", "input": "table users(id, name, age)", "output": "SELECT ..."}
```

检查每个答案是否满足指令要求，以及是否正确使用了提供的输入。复核时同时关注格式有效性、事实正确性和任务覆盖情况。

<a id="change-one-generation-setting"></a>

## 调整一个生成设置

单文件脚本包含 `NUM_INSTRUCTIONS`、`INSTANCES_PER_INSTRUCTION`、`SEED_FILE`、`TEMPERATURE` 和 `MAX_TOKENS` 等设置。调整其中一项，将结果存入新输出目录，比较保留下来的候选数量及其任务覆盖。需要聚焦某个领域时，使用包含具体任务的种子文件。

将种子列表、生成设置、模型 ID 和输出文件一起保存。增加指令数量或 token 上限时，观察 API 用量。加入训练集前，逐条复核答案正确性、重复样本和依据不足的样本。单次生成更多记录不代表质量改善；同一输入和设置下的模型波动也要记入对照。

<a id="references"></a>

## 参考资料

- [Self-Instruct：用自生成指令对齐语言模型](https://arxiv.org/abs/2212.10560)
- [Self-Instruct 原始实现](https://github.com/yizhongw/self-instruct)

继续学习 [Alpaca 数据构造](../alpaca_data/README.md)。


## 在自己的项目中使用

为同一个业务任务准备人工种子与独立检查标准，检查新增样本是否覆盖了不同输入和边界情况。将内容错误与格式不合格分开统计，再参考[偏好数据](../preference_data/README.md)学习怎样保留候选、来源和人工判断。

[主题目录](../README.md) · [课程首页](../../README.md)
