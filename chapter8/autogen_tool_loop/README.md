<a id="lesson-2-framework-tool-calling-mcp-and-cli-skills"></a>

# 框架工具调用

沿用[手写函数调用](../manual_tool_loop/README.md)的数列和统计任务，用 AutoGen 管理函数注册、执行和反馈。本练习只比较框架接管了哪些流程。

先按[模型配置](../../README-DEEPSEEK.md)导出 `OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_API_KEY`，再从仓库根目录运行。

## 工程任务

把手写循环交给框架后，代码变短了，但数据正确性与终止行为仍需要验证。

在 [autogen_function_call_demo.py](autogen_function_call_demo.py) 中，保持模型、--count、--seed 和约束，比较手写引擎与 AutoGen。

在相同题目、模型和种子下比较两份实际轨迹，说明框架接管了什么、仍需自行保证什么。

## 动手 · AutoGen 接管工具调用

```bash
python -m pip install -r chapter8/autogen_tool_loop/requirements.txt
python chapter8/autogen_tool_loop/autogen_function_call_demo.py --count 18 --seed 42 --output chapter8/autogen_tool_loop/results/baseline.json
```

本课复用手写函数调用练习的 `generate_numbers` 和 `calculate_stats` 纯函数，以类型注解包装后注册，由 `AssistantAgent` 选择函数，`UserProxyAgent` 执行函数并返回结果。查看程序里的 `register_function`，指出 `caller` 与 `executor` 各自负责什么。

把终端记录与手写函数调用练习对照，核对生成的数字是否确实进入统计函数，以及最后的成绩判定是否符合平均值 60—80、最小值至少 30 的条件。解释框架接管了哪些消息和调用流程。[函数与调用循环的原理](#autogen-loop)

<a id="autogen-loop"></a>

### 相同任务的两种实现

两课使用相同的 `generate_numbers` 和 `calculate_stats`，并采用平均分 60—80、最低分至少 30 的判定条件。保持任务和工具固定，比较手写自问自答循环与框架管理的调用流程。

| 观察项 | 手写实现 | 本课 AutoGen 实现 |
|---|---|---|
| 函数描述 | 显式维护函数注册表和参数说明 | `register_function` 结合函数和类型注解生成工具描述 |
| 动作格式 | 解析约定的 `Follow up` 文本与 JSON | 使用模型的工具调用消息 |
| 结果反馈 | 把 `Intermediate answer` 加入历史 | 执行端把函数结果送回会话 |
| 对话管理 | 自行累积历史和控制循环 | 智能体对话管理与轮次限制 |
| 参数与错误 | 自行解析参数，执行函数并处理错误 | 结合工具描述、执行函数和框架配置处理 |
| 完成条件 | 识别约定的最终答案标记 | 配置终止条件与最大轮次 |

### 函数注册与角色分工

手写实现需要在注册表中维护函数引用、描述和参数。框架版本把实际函数分别连接到调用者和执行者。

```python
# 手写版本的注册思路
FUNCTIONS = {
    "generate_numbers": {
        "func": generate_numbers,
        "desc": "Generate random numbers",
        "params": {"count": "Number count"},
    }
}

# 本课的框架注册
register_function(
    generate_numbers,
    caller=assistant,
    executor=user_proxy,
    name="generate_numbers",
    description="Generate a list of random numbers",
)
```

`AssistantAgent` 选择函数并构造调用，`UserProxyAgent` 执行函数后提供观察结果。类型注解为模型提供参数的类型与描述。检查函数实现中的参数处理与错误返回，解释框架配置和业务函数各自承担的验证工作。

### 从推理到动作再到观察

ReAct 用“推理—动作—观察”描述工具使用中的反馈循环。把这个视角应用到本课轨迹，可以看到模型先获取数据，再依据观察选择统计函数，最后解释结果。

```text
分析任务
  → Suggested tool call: generate_numbers
  → 执行函数并返回数字
  → 根据返回数据选择下一步
  → Suggested tool call: calculate_stats
  → 执行统计并返回结果
  → 核对条件，输出结论
```

本课程序通过模型原生工具调用和框架会话完成这一循环。追踪每次调用中的数字是否一致，说明统计函数如何收到上一轮的数据。再查看 `max_consecutive_auto_reply`、`is_termination_msg` 和调用轮次，观察结束条件如何影响运行。

### 学习重点

保持函数和任务不变，可以把注意力放在消息格式、函数注册、参数处理、会话管理与错误处理上。手写版本便于逐步观察这些环节，框架版本便于把它们组织成可复用的智能体协作流程。

对照基线轨迹时，标出函数选择、参数、执行结果和最终结论，说明框架接管了哪些工作。接下来的 MCP 练习沿用同一组观察项，继续检查工具移到独立进程后，描述、调用与结果怎样跨越进程边界。

两种实现使用同一套独立业务检查。`--output` 中的 `trace` 来自实际执行函数，`validation` 对照固定种子数列和独立统计计算，记录工具调用及失败；`elapsed_seconds` 是整个流程耗时。模型的最终文字结论仍要与 `reference_qualified` 分开核对。

通过 `--max-steps` 改变预算时，手写程序按模型决策步计数，AutoGen 按框架对话轮计数，两个数字的单位不同；不能按相同预算数值直接断言效率优劣。先确认两者都完成同一任务，再对照实际轨迹和总耗时。

## 预测、单变量对照与独立验收

先预测框架是否还需要分别注册调用者和执行者。运行后检查 `baseline.json` 中的实际工具消息，核对18个分数、种子42、0—100范围，以及平均值和最小值；再用同一数列独立复算合格条件。

与手写循环比较时，两边都使用 `--count 18 --seed 42` 和同一模型，不同时换任务。程序两侧共用纯计算函数，改变的是调用循环的管理方式。记录消息格式、参数处理、实际执行和结束条件；不因代码更短就断言 Token、耗时或正确性更好。

随后只将框架版本的数量改为20，保存到新文件，再用同样参数运行手写版本，核对两边实际数据。框架回合通过 `TERMINATE` 结束，不把包含“完成”的普通分析文字或 content 为空的工具调用误当作终止。

对照两侧调用轨迹及一份参数/结果对照。没有真实工具结果、只有最终回答时不能判定通过。每次运行是新的会话，报告目录可独立删除，不影响源码或另一课的输出。

完成后可进入[MCP 工具发现与调用](../../chapter9/mcp_tools/README.md)。

## 在自己的项目中使用

将一个实际工具任务同时接入手写循环与当前框架，保留同样的输入、纯函数和业务检查。比较参数处理、错误恢复、停止方式和耗时，再决定框架提供的管理能力是否值得引入；跨进程服务参考[MCP 工具](../../chapter9/mcp_tools/README.md)。

[主题目录](../README.md) · [课程首页](../../README.md)
