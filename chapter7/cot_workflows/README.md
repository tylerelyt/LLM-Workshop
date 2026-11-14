<a id="lesson-4-advanced-reasoning-with-llms"></a>

# CoT 与推理编排

本课学习如何组织大模型的推理过程，通过多轮交互、任务拆解和中间结果校验来处理复杂问题。

## 工程任务

把一个需求拆成多次模型调用后，早期要求可能没有进入后续步骤。

在 [example2.py](example2.py) 中，固定问题与模型，只改变一处中间结果是否传到后续步骤。

指出一条确实发生的信息丢失，并说明哪些内容应在交接时保留、哪些可以省略。

## 学习目标

- **思维链（CoT）**：通过基础 CoT 提示引导模型逐步思考。
- **多轮推理**：通过多次交互积累上下文，完成较大的任务。
- **任务拆解**：将复杂任务分成模型可以处理的较小子任务。
- **带检查点的推理**：每一步都先校验模型输出，再继续执行，以提高最终结果的可靠性。

---

<a id="file-descriptions"></a>

## 文件说明

- `example1.py`：演示基础的“让我们逐步思考”提示。
- `example2.py`：通过多轮推理，在多个步骤之间积累信息。
- `example3.py`：将任务拆开，为不同部分分配不同角色。
- `example4.py`：演示带检查点的推理流程，逐步验证输出，再纳入最终结果。
- `requirements.txt`：列出本课所需的 Python 依赖。

---

<a id="setup-and-execution"></a>

## 环境准备与运行

在仓库根目录安装 `chapter7/cot_workflows/requirements.txt` 中的依赖，并设置课程 `OPENAI_*` 模型接口。[模型配置](../../README-DEEPSEEK.md#setup)

```bash
python chapter7/cot_workflows/example1.py
python chapter7/cot_workflows/example2.py
python chapter7/cot_workflows/example3.py
python chapter7/cot_workflows/example4.py
```

1. 检查单次提示给出的和是否为 15。
2. 阅读三轮预算对话，核对结果是否为 5 包、总计 195 美元、剩余 5 美元。将场地费用改为 45 美元，再看最终建议是否变化。
3. 检查分析师向开发者交接的内容。平均值为 21，建议的函数应在平均值等于阈值时触发提醒。
4. 依次查看计划步骤、候选结果和检查点判定。最终应在桌面放置 24 套，含备用共 27 套，总费用为 54 元。先独立复算这些值，再运行故障注入对照。

```bash
python chapter7/cot_workflows/example4.py --inject-error
```

该开关只把第二步候选结果替换为错误的 26 套。保留原模型与任务，检查验证消息是否真的包含这个候选，以及检查失败后是否停止生成后续步骤和最终汇总。`PASS` 来自模型评议，还需与你独立复算的值对照；若错误候选仍通过，就记录这次漏检。

在示例 3 中，只把阈值从 `20` 改为 `21`，保留读数 `18、21、24`。检查分析师到开发者的交接是否保留“平均值大于等于阈值”，并用示例值和等于阈值的断言核对生成代码。保留交接内容和一个正常／失败检查点的轨迹，解释哪部分由应用显式传入历史。

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

为自己的多步任务写出独立可检查的中间产物，追踪每次交接是否保留原始约束。步骤固定时对照[顺序工作流](../../chapter9/sequential_planning/README.md)；下一步依赖外部结果时，使用[工具循环](../../chapter8/manual_tool_loop/README.md)观察真实反馈。

[主题目录](../README.md) · [课程首页](../../README.md)
