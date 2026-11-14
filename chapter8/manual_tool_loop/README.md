<a id="lesson-1-manual-function-call-implementation"></a>

# 手写函数调用

手写 Self-Ask 循环，观察函数描述、JSON 动作、实际 Python 执行与结果反馈。模型决策和程序计算分开记录；本课不要求暴露模型的内部思考。

## 工程任务

生成数列与统计数列分属两次函数调用。模型传错参数仍可能得到格式正确的统计结果。

在 [function_call_workshop.py](function_call_workshop.py) 中，固定数列数量、随机种子、任务和模型，只修改 process_parameters 的前序结果引用处理。

用共同的业务检查核对实际数列、统计输入与独立复算值，最后单独核对模型结论。

## 可运行起点

提供 `generate_numbers`、`calculate_stats`、函数注册表和五轮上限的调用循环。先按[模型配置](../../README-DEEPSEEK.md)导出课程 `OPENAI_*` 变量，从仓库根目录运行：

```bash
python -m pip install -r chapter8/manual_tool_loop/requirements.txt
python chapter8/manual_tool_loop/function_call_workshop.py --count 18 --seed 42 --output chapter8/manual_tool_loop/results/baseline.json
```

数据范围固定为 0—100，平均分在 60—80 且最低分至少 30 时才合格。接口请求失败与模型动作格式错误分开报错。环境错误不作为“模型不会调用函数”的证据。

## 沿调用链观察

先预测种子固定时重复运行是否得到同一份数列，再运行一次。沿下面的路径记录实际发生的行为：

```text
用户任务 → Follow up JSON → 解析与参数引用处理 → Python 函数
        → Intermediate answer → 下一轮模型输入 → 最终结论
```

- `trace[].parameters` 是参数处理后真正传入函数的内容。核对统计函数的数列是否等于生成函数的真实输出。
- `trace[].result` 与 `messages` 展示工具反馈怎样进入下一轮；模型结论不能作为统计值的来源。
- 程序独立复算平均值、最小值和合格条件。它会拒绝缺少工具调用或数据流不一致的执行；模型的文字结论仍需逐项对照。

<a id="self-ask-消息与数据流"></a>

## 改一个变量

保持模型与种子不变，只把数量从 18 改成 20：

```bash
python chapter8/manual_tool_loop/function_call_workshop.py --count 20 --seed 42 --output chapter8/manual_tool_loop/results/count20.json
```

比较生成数列、统计输入和最终判断。每次运行创建新的引擎；不要把上一轮历史追加进本轮。代码中的 `get_function_descriptions`、`parse_function_call`、`process_parameters`、`execute_function` 分别负责描述、解析、明确的前序结果引用与执行。

两种实现使用同一套独立业务检查。`--output` 中的 `trace` 来自实际执行函数，`validation` 对照固定种子数列和独立统计计算，记录工具调用及失败；`elapsed_seconds` 是整个流程耗时。模型的最终文字结论仍要与 `reference_qualified` 分开核对。

通过 `--max-steps` 改变预算时，手写程序按模型决策步计数，AutoGen 按框架对话轮计数，两个数字的单位不同；不能按相同预算数值直接断言效率优劣。先确认两者都完成同一任务，再对照实际轨迹和总耗时。

## 行为验收

保留两份报告，并独立复算其数据。记录数量改变后判断是否变化，不预设一定变化。若模型跳过工具、传错数列或未给出可复算统计，保留失败轨迹并解释断在哪一步。

继续完成[框架工具调用](../autogen_tool_loop/README.md)，比较时使用相同的 `--count`、`--seed`、模型和题目约束。复跑请使用新的 `--output` 文件名；结果位于本课 `results/`，只清理自己的输出。

## 在自己的项目中使用

为自己的两步计算任务先写纯函数与独立结果检查，再注册给调用循环。构造一次参数引用错误，确认检查器能发现“执行成功但数据错误”；接着在[框架版本](../autogen_tool_loop/README.md)中保留相同业务检查，比较更换运行机制后的表现。

[主题目录](../README.md) · [课程首页](../../README.md)
