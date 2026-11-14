<a id="lesson-3-alpaca-training-data-construction"></a>

# Alpaca 数据格式

将原始示例转换为监督微调的统一格式。本练习将任务指令与输入分开，保留预期答案，用同一批构造样例对照关闭和开启基础过滤时的行为。

## 工程任务

格式转换可能把示例答案混入目标输入，也可能留下重复记录与空答案。

在 [alpaca_constructor.py](alpaca_constructor.py) 中，固定输入数据，只切换 enable_filtering。

用原始记录、字段映射和实际过滤原因解释保留或拒绝，区分格式合格与内容可训练。

## Alpaca 数据结构

| 字段 | 含义 |
|---|---|
| `instruction` | 需要完成的任务 |
| `input` | 可选的上下文或目标文本，未使用时用空字符串表示 |
| `output` | 预期答案 |

下面是一条不含额外输入的示例。

```json
{
  "instruction": "Explain what machine learning is",
  "input": "",
  "output": "Machine learning uses algorithms to learn patterns from data and make predictions or decisions."
}
```

翻译记录将指令与原始句子分开。

```json
{
  "instruction": "Translate the following text to English",
  "input": "人工智能正在改变我们的世界。",
  "output": "Artificial intelligence is changing our world."
}
```

<a id="run-the-conversion"></a>

## 运行转换

激活课程 Python 环境后，从仓库根目录运行。以下步骤在本地转换数据。第一条数据处理命令会重新生成Few-shot 指令数据练习的 Few-shot 输入，因此也可以在新终端中完整运行此示例。

```bash
python -m pip install \
  -r chapter5/fewshot_data/requirements.txt \
  -r chapter5/alpaca_data/requirements.txt
workshop_out="$(mktemp -d)"
python chapter5/fewshot_data/construct_fewshot.py \
  --input-file chapter5/fewshot_data/data/sentiment_demo.json \
  --task-type sentiment \
  --output-path "$workshop_out/fewshot.jsonl"
python chapter5/alpaca_data/alpaca_constructor.py \
  --input-file "$workshop_out/fewshot.jsonl" \
  --conversion-type fewshot_to_alpaca \
  --output-path "$workshop_out/alpaca.jsonl"
```

如果保留了Few-shot 指令数据练习的输出，可将该文件直接传给 `--input-file`。对照一条原始记录及其转换结果。目标句子应移入 `input`，其 `正面` 或 `负面` 标签应保留在 `output` 中。

终端默认展示保留和过滤各一条实际记录，逐项对照原始数据与 `instruction`、`input`、`output`，同时给出实际过滤原因；本轮没有过滤记录时会直接说明。通过字段和重复规则仍需另行核对答案内容。


<a id="choose-a-conversion-type"></a>

## 选择转换类型

加载器接受 CSV、JSON 和 JSONL。选择与原始数据结构对应的转换器。

| 转换类型 | 原始结构 | 转换行为 |
|---|---|---|
| `fewshot_to_alpaca` | Few-shot `instruction` 和目标 `output` | 从组合提示中提取任务描述与目标输入 |
| `qa_to_alpaca` | 问题与答案对 | 使用统一的回答指令，将问题放入 `input` |
| `chat_to_alpaca` | `conversations` 或 user/assistant 字段 | 将首轮用户与助手对话转换为一条响应记录 |
| `classification_to_alpaca` | 文本与类别标签 | 使用分类指令，将标签保留为 `output` |

转换器支持含有额外输入和不含额外输入的记录。适配其他数据集时，检查各转换函数接受的字段别名。

<a id="quality-control-and-verification"></a>

## 质量控制与验收

质量过滤要求任务描述至少有五个字符，且答案非空。它限制指令与输出的长度，再按指令和输入的组合去重。因此，不同目标句子可以保留相同指令，简短的有效情感标签也能保留。

提交一条原始记录、它的转换结果以及保留的示例数量。核对转换是否保留了目标文本和答案。再为一个小数据集选择另一种转换类型，检查生成的指令是否表达了预期任务。

### 固定输入，对照过滤开关

先构造两条不同输入、一条完全重复和一条空答案记录。运行前预测开启过滤后会保留几条，以及简短情感标签是否会被保留。

```bash
python - "$workshop_out" <<'PY_LOCAL'
import json
from pathlib import Path
import sys
records = [
    {"text": "很喜欢", "label": "正面"},
    {"text": "很失望", "label": "负面"},
    {"text": "很喜欢", "label": "正面"},
    {"text": "感觉一般", "label": ""},
]
Path(sys.argv[1], "classification-check.json").write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
PY_LOCAL
python chapter5/alpaca_data/alpaca_constructor.py \
  --input-file "$workshop_out/classification-check.json" \
  --conversion-type classification_to_alpaca --no-enable-filtering \
  --output-path "$workshop_out/unfiltered.jsonl"
python chapter5/alpaca_data/alpaca_constructor.py \
  --input-file "$workshop_out/classification-check.json" \
  --conversion-type classification_to_alpaca \
  --output-path "$workshop_out/filtered.jsonl"
```

第一轮应有四条，第二轮应保留两条不同目标文本及其两字标签。再将重复记录的标签改成相反的值，检查按指令和输入去重会保留哪一个答案。为这类冲突写出自己的复核决定，不能用去重后的条数代替答案正确性。

修改范围集中在 `extract_target_input` 和 `filter_quality`。使用Few-shot 指令数据练习的问答或翻译模板时，选择一条含引号或换行的目标文本，逐字对照转换前后的目标内容，确保示例答案没有误入 `input`。提交原始记录、转换结果、过滤前后差异及冲突处理理由；换一轮输出文件名后重跑。

复核后的 JSONL 可用于监督微调，包括 LoRA 或全参数训练流程。根据所用训练器，检查数据集的混合方式和字段约定。将转换后的示例带入[偏好数据构造](../preference_data/README.md)。

<a id="references"></a>

## 参考资料

- [Stanford Alpaca 项目](https://github.com/tatsu-lab/stanford_alpaca)
- [清洗后的 Alpaca 数据集](https://huggingface.co/datasets/yahma/alpaca-cleaned)

终端默认展示保留和过滤各一条实际记录，逐项对照原始数据与 `instruction`、`input`、`output`，同时给出实际过滤原因；本轮没有过滤记录时会直接说明。通过字段和重复规则仍需另行核对答案内容。

## 在自己的项目中使用

为自己的原始数据写一个小型格式适配，逐条追溯 instruction、input、output 的来源。检查转换是否丢失任务限制，并与[Self-Instruct](../self_instruct/README.md)产生的记录使用同一套内容复核标准；结构相同并不意味着可以直接混合作为训练集。

[主题目录](../README.md) · [课程首页](../../README.md)
