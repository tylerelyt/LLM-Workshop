<a id="lesson-1-automated-few-shot-instruction-data-construction"></a>

# Few-shot 指令数据

将结构化示例转换为指令记录，并逐条证明目标文本和标签在构造后仍对应原始数据。每条记录包含任务描述、带答案的示例和目标输入，复核后再带入Alpaca 数据格式练习。

## 工程任务

将带标签数据改写成指令样本时，示例、目标输入和目标答案可能被错误配对。

在 [construct_fewshot.py](construct_fewshot.py) 中，固定原始记录与随机种子，只改变 num_examples。

逐条核对原始标签与生成记录，说明增加示例数量是否值得额外的输入长度。

## 脚本的处理流程

- 为情感分析、通用分类、问答和翻译选择对应的任务模板。
- 为每条目标数据配对另一行数据，作为 Few-shot 示例。
- 读取 CSV、JSON、JSONL 和 TSV 文件，识别常见字段名。
- 在 JSONL 的每一行写入一个含有 `instruction`、`input` 和 `output` 的对象。

自带的情感数据集包含英文、中文和混合语言评论，涵盖正面、负面标签以及情感表达复杂程度不同的句子。数字标签 `0` 转换为 `负面`，`1` 转换为 `正面`。

<a id="run-the-exercise"></a>

## 运行练习

激活课程 Python 环境后，从仓库根目录运行。本课在本地转换数据。

```bash
python -m pip install -r chapter5/fewshot_data/requirements.txt
workshop_out="$(mktemp -d)"
python chapter5/fewshot_data/construct_fewshot.py \
  --input-file chapter5/fewshot_data/data/sentiment_demo.json \
  --task-type sentiment --seed 42 \
  --output-path "$workshop_out/fewshot.jsonl"
```

保留 `workshop_out` 的值和其中的 `fewshot.jsonl`，供Alpaca 数据格式练习使用。默认每条指令配对一个示例，原始数据至少需要两条。`--num-examples` 控制配对数量，并要求原始记录比该数量多至少一条；`--max-samples` 限制处理条数。固定 `--seed` 后，配对和模板抽样可复现。

运行后，终端展示本轮一条实际原始记录、生成的含示例指令和沿用原标签的目标答案。先核对示例与目标的配对，再打开 JSONL 检查其余记录。


<a id="follow-the-construction-process"></a>

## 跟踪构造过程

1. 选择任务类型，检查哪些原始字段提供输入和答案。
2. 从模板集合中选择一条任务描述。
3. 为目标行配对一个示例，将两者放入指令。
4. 在 `output` 中保留目标答案，并将记录写成 JSONL。

| 任务类型 | 常见输入字段 | 常见答案字段 |
|---|---|---|
| `sentiment` | `sentence`, `text`, `content` | `label`, `category`, `target` |
| `classification` | `text`, `document`, `input` | `label`, `class`, `output` |
| `qa` | `question`, `query`, `prompt` | `answer`, `response`, `output` |
| `translate` | `source`, `en`, `original` | `target`, `zh`, `translation` |

提取函数还接受其他字段别名。接入新数据集时，先将它的字段与 `extract_input_output` 对照，再选择任务类型。

<a id="inspect-a-record"></a>

## 检查一条记录

下面这条原始数据的输出标签应保留负面情感。

```json
{"sentence": "The plot is predictable and the acting is dull.", "label": 0}
```

下面展示一种可能生成的记录。未固定随机种子时，模板和配对示例可能变化。

```json
{
  "instruction": "判断下面这句话表达的是积极情绪还是消极情绪？\n例子：\n句子：\"A masterpiece, a profoundly moving film.\" 情绪：正面\n现在请判断下面这个句子：\n句子：\"The plot is predictable and the acting is dull.\" 情绪：",
  "input": "",
  "output": "负面"
}
```

此时目标句子嵌在 `instruction` 中。Alpaca 数据格式练习会将它提取到 Alpaca 的 `input` 字段。

<a id="experiment-and-verify"></a>

## 实验与验收

先保持输入数据、任务类型和随机种子相同，只关闭模板多样化，将第二份输出存到独立文件。

```bash
python chapter5/fewshot_data/construct_fewshot.py \
  --input-file chapter5/fewshot_data/data/sentiment_demo.json \
  --task-type sentiment --seed 42 --no-template-variety \
  --output-path "$workshop_out/fewshot-fixed-template.jsonl"
```

比较两份文件中每条指令的第一行，固定模板这一轮应全部使用 `FEWSHOT_TEMPLATES["sentiment"][0]`。同一随机种子下，配对示例、目标输入和标签应保持一致，差异只出现在任务描述。用这一对照验收模板开关，再评价措辞是否清楚。

从原始数据中选一条正面、一条负面和一条混合语言评论，定位它们各自生成的指令。标出任务描述、示例、目标输入和预期答案，确认目标文本保留、`output` 与原始标签对应，并确认示例不是目标行本身。运行正常结束或 JSONL 能被解析，只证明构造路径完成；原始标签是否合理仍由你复核。

可以修改 `FEWSHOT_TEMPLATES` 的一条任务描述，保持同一随机种子重跑。保留这项措辞修改的前后记录，解释任务要求变了什么，以及数据内容和标签为什么仍对应原始样本。输出目录隔离每轮结果，重跑时使用新的文件名以保留对照。

继续学习 [Self-Instruct 数据构造](../self_instruct/README.md)，或直接将本课输出用于 [Alpaca 格式转换](../alpaca_data/README.md)。


## 在自己的项目中使用

选择一个有输入与标签的实际任务，先检查少量人工样本的类别边界，再构造指令。保留未用于示例的测试输入，用[基础提示](../../chapter6/basic_prompting/README.md)比较加入示例前后的行为，避免用被复制进提示的答案验证效果。

[主题目录](../README.md) · [课程首页](../../README.md)
