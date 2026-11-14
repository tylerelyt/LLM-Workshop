<a id="lesson-3-implementing-a-react-agent"></a>

# ReAct Agent

本课从零实现 ReAct（推理与行动）Agent，让模型分析问题、通过工具获取信息，再形成最终答案。

## 工程任务

任务同时需要查到事实和完成计算。你要确认答案真的经过了工具，而非模型口头声称已查询。

在 [example1.py](example1.py) 中，固定题目与模型，只改变 query 的 max_turns。

从实际 Observation 复算最终结果，并解释轮次不足时系统应如何结束。

## 学习目标

- **ReAct 流程**：理解“思考 → 动作 → 观察”这一核心循环，对应输出中的 `Thought`、`Action` 和 `Observation`。
- **工具创建与注册**：建立自定义工具的注册表，供 Agent 调用。
- **动态提示**：构造系统提示，向模型说明 ReAct 的运行方式、可用工具和输出格式。
- **Agent 循环**：解析模型输出，执行动作，再将观察结果放回上下文。

---

<a id="file-descriptions"></a>

## 文件说明

- `example1.py`：从零实现完整的 ReAct Agent，通过查找科学常数并执行计算来解题，展示工具注册、动态提示生成和主推理循环。
- `requirements.txt`：列出本课所需的 Python 依赖。

---

<a id="setup-and-execution"></a>

## 环境准备与运行

在仓库根目录安装 `chapter8/react_agent/requirements.txt` 中的依赖，并设置课程 `OPENAI_*` 模型接口。[模型配置](../../README-DEEPSEEK.md#setup)

```bash
python chapter8/react_agent/example1.py
```

跟踪 `Action` 和 `Observation`。模型先查询两个常数，再将算式交给计算器。程序逐次提供工具结果，并打印模型完整的 `Answer`。将最终答案与计算器返回的约 `1.98645e-25 J·m` 对照。

`lookup_fact` 读取程序内的教学常数表，`calculate` 解析算式并实际计算。先根据轨迹画出“问题 → 查表参数 → 查表结果 → 计算表达式 → 数值结果 → 答案”。保留同一问题，只把循环预算降到一轮。

```bash
python chapter8/react_agent/example1.py --max-turns 1
```

第一轮工具执行后，模型还需要后续请求读取观察并继续。检查预算用尽时程序是否明确结束，而不是把未完成步骤当成最终答案。再恢复默认预算，核对计算表达式是否确实使用工具查到的常数。

还可以用 `--question` 改问地球和月球的质量比，继续使用同一工具注册表。验收以实际查表与计算结果支持最终答案为准；最终文字中出现正确数值，但轨迹缺少工具动作时，应记录为未完成工具使用目标。

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

选一个需要外部信息才能完成的任务，为工具准备可独立核对的返回值，检查模型是否依据实际观察选择下一步。用[手写工具循环](../manual_tool_loop/README.md)进一步检查参数处理与停止条件，再决定采用哪种动作格式。

[主题目录](../README.md) · [课程首页](../../README.md)
