<a id="lesson-3-code-interpreter---ai-dynamic-programming"></a>

# 代码解释器

## 工程任务

生成一个背包求解程序之后，还要确认它真的执行、满足容量限制并达到最优价值。

在 [code_interpreter_workshop.py](code_interpreter_workshop.py) 中，固定问题、容量与模型，只改变执行器的 max_consecutive_auto_reply；记录每轮实际生成的程序，保留 Docker 执行和结果校验。

把语法通过、执行成功与结果正确分开判断，解释循环预算和真实反馈的作用。

## 学习目标与起点

让模型根据同一组背包约束生成 Python 程序，再用实际容器输出核对物品组合、总重量和最优价值。先前工具调用课执行预定义函数，本课观察“生成代码—执行—反馈—核对”怎样连成一条执行链。

本课有生成和 Docker 执行两种运行方式。它们各自启动新的模型会话。先从仓库根目录查看教学题目与独立枚举参考结果，此命令不调用模型或 Docker。

```bash
python chapter8/code_interpreter/code_interpreter_workshop.py --show-task
```

背包容量默认 10 千克，每件物品最多选一次。

| 物品 | 重量（千克） | 价值 |
|---|---|---|
| 1 | 2 | 3 |
| 2 | 3 | 4 |
| 3 | 4 | 5 |
| 4 | 5 | 6 |
| 5 | 1 | 2 |

先手工求一组可行解，再核对参考结果。容量 10 时，物品 1、2、3、5 的总重量为 10，总价值为 14。模型需要输出一行 `RESULT_JSON=`，字段为 `selected_items`、`total_weight` 与 `max_value`，用于后续对照真实执行结果。

## 生成代码并检查

使用 Python 3.11 或 3.12。安装本课依赖，在当前终端导出课程的 `OPENAI_*` 模型配置。以下命令都从仓库根目录运行。[模型配置](../../README-DEEPSEEK.md)

```bash
python -m pip install -r chapter8/code_interpreter/requirements.txt
LAB_DIR=$(mktemp -d)
python chapter8/code_interpreter/code_interpreter_workshop.py --output-dir "$LAB_DIR/generated"
```

打开 `knapsack_generated.py`，检查算法怎样表示每件物品最多取一次、容量上限、状态转移和组合还原。`report.json` 的状态为 `generated_only`，这一轮只完成生成与语法检查。把生成代码与手工可行解对照，保留题目、代码和运行记录。

## 运行代码并观察反馈

本课依赖包含 Python 的 Docker SDK。安装并启动 Docker 后，在同一终端检查连接，再运行执行模式。

```bash
docker info
python chapter8/code_interpreter/code_interpreter_workshop.py --execute --output-dir "$LAB_DIR/executed"
```

`--execute` 会启动一次新的代码生成和容器执行流程。程序在模型调用前检查 Docker SDK 和服务连接。若 CLI 能连接而 Python 检查失败，核对当前 Docker 上下文对应的 `DOCKER_HOST`。

在对话中依次找出代码块、容器标准输出或错误、模型依据执行结果给出的回答。打开本轮 `report.json`，查看 `executions` 中由执行器实际返回的退出码与输出。检查器从最后一次成功执行的 `RESULT_JSON` 还原所选物品，独立计算重量与价值，并用五件物品的枚举结果核对最优值。没有实际执行记录、结果格式不完整或约束不成立时，以失败状态结束并留下诊断。

`execution_verified` 表示本次实际输出通过了上述业务核对。仍需阅读生成的算法，解释它如何得到结果。模型最终声明完成、生成文件存在或代码能解析，都不能单独作为本课验收依据。

## 只改变容量

保持五件物品不变，将 `--capacity` 从 `10` 改为 `8`。先预测最优价值，再用 `--show-task --capacity 8` 核对独立枚举结果，之后在新目录运行生成与执行。对照两轮的题目、实际执行输出与所选组合。

学员本轮只改 `--capacity`，需要修改算法时编辑生成代码的副本。`reference_solution` 和执行记录器是讲师提供的验收基础设施。不同轮次使用不同的 `--output-dir` 保留证据，重跑时新建目录即可回到无历史执行记录的起点。

<a id="code-interpreter-的工作方式"></a>

## 代码解释器的工作方式

```text
任务约束 → 模型选择算法 → 生成代码 → 容器执行 → 返回输出或错误 → 模型分析
```

| 能力 | 观察点 |
|---|---|
| 动态编程 | 模型是否根据本次容量生成了合适的求解程序 |
| 算法与数据结构 | 状态、边界条件和结果还原是否正确 |
| 调试 | 执行错误是否返回给模型，后续代码是否修正对应问题 |
| 结果展示 | 物品组合、重量、价值是否与实际执行输出一致 |

本课的 `AssistantAgent` 生成代码，`RecordingExecutor` 在 `UserProxyAgent` 执行路径上记录真实结果。阅读 `create_code_interpreter`，说明执行配置、工作目录、最大轮次和终止条件各起什么作用。[实现代码](code_interpreter_workshop.py)

## 扩展：城市交通最短路径

把任务换成一张可手工核对的小型城市交通图，先保留边权表，再要求模型实现 Dijkstra 算法，输出路径与总距离并绘图。改变一条边权后重跑，核对路径、总距离和图上的数值。

这项扩展需要根据最短路径约束另设验收，背包题的 `verify_execution` 不能用于证明路径正确。比较需求分析、算法选择、代码实现和执行反馈各自留下了什么证据。

## 交付与验收

提交容量 10 和容量 8 的题目、生成代码、实际执行输出、运行记录与人工复算。说明执行反馈是否引发修正，以及容量变化后结果是否符合相同约束。若本机只能完成生成，保留 `generated_only` 记录，实际执行与结果核对仍是待完成步骤。

下一课把“产出—检查—反馈”用于内容评估，并保存改进经验。[反思系统](../../chapter9/reflection/README.md)

## 在自己的项目中使用

选择一个有独立结果判定方法的小型程序任务，先定义输入、约束与测试，再让模型生成并执行。需要多次读取和修改项目文件时，继续做[编程 Harness](../../chapter9/mcp_harness/README.md)，保留由任务方定义的独立检查。

[主题目录](../README.md) · [课程首页](../../README.md)
