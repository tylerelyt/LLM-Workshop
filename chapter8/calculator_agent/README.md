# 计算工具 Agent

观察模型提出动作、Python 执行表达式、模型依据真实结果回答的边界。本课的起点是已有计算函数与 Agent；学习任务是追踪并改变一次真实工具调用。

## 工程任务

计算任务要求准确数值，你要检查计算是否由工具完成、结果是否真实回填。

运行 [calculator_agent.py](calculator_agent.py)，固定表达式和模型，只改变 `--max-steps`，比较工具执行与停止条件。

独立复算表达式，决定是否需要工具，以及轮次限制是否妨碍了真实执行。

## 环境与第一次运行

使用 Python 3.11 或 3.12，按[模型配置](../../README-DEEPSEEK.md#setup)配置聊天服务。模型请求直接使用课程的 Chat Completions 客户端。

```bash
python -m pip install -r chapter8/calculator_agent/requirements.txt
python chapter8/calculator_agent/calculator_agent.py --expression '37593 * 67' --output /tmp/calculator-baseline.json
```

默认使用课程配置的模型，`--model` 可覆盖模型 ID，`--max-steps` 设置 Agent 的最大迭代次数（默认 5）。`--output` 保存真实工具调用、独立参考值、最终回答与耗时；工具结果核对通过后，仍需检查最终文字是否准确。依赖缺失、服务连接失败与模型不可用属于环境问题。

## 先预测，再改一个变量

1. 独立算出 `37593 * 67` 的参考值 `2518731`，预测模型是否会实际调用工具。
2. 在记录中找到 `Action`、`Action Input`、`TOOL_RESULT` 和最终答案。`TOOL_RESULT` 由计算函数执行后打印，不能用模型自己写出的 Observation 代替。
3. 保持服务、模型和 Agent 配置不变，只改变表达式：

```bash
python chapter8/calculator_agent/calculator_agent.py --expression '(17 + 23) * 5'
```

这次参考值是 `200`。若模型没调用工具，即使答对，也未完成本课的工具调用观察；保留实际结果再调整请求，而不是补造工具日志。

## 验收与重跑

保留两组表达式、工具实际参数、`TOOL_RESULT` 与模型答案。用独立计算核对数值，并解释哪一步由模型选择、哪一步由 Python 计算。每次运行是新进程，重跑不共享对话。只读代码的 `calculate_expression` 可核对计算机制，无需修改模型接口或解析器。

## 在自己的项目中使用

选择包含边界输入的实际计算问题，先建立参考结果，再检查工具参数与最终文字。若多步工具之间需要传递数据，进入[手写工具循环](../manual_tool_loop/README.md)，增加独立的数据流检查。

[主题目录](../README.md)
