# 语言智能体的构建

把模型的一次决策接入实际执行，并用观察和状态支持后续决策。先完成[模型服务与 Session](../chapter4/model_service/README.md)，区分模型输入与应用保存的历史。

## 先看执行，再管理状态

从[手写工具循环](manual_tool_loop/README.md)开始，沿模型动作、参数处理、Python 执行和结果回填检查同一个任务。随后用[框架工具调用](autogen_tool_loop/README.md)完成相同任务，比较框架管理了什么，哪些业务检查仍要自己实现。

| 要研究的机制 | 独立实验 |
| --- | --- |
| 动作与外部观察怎样组织 | [ReAct](react_agent/README.md)、[计算工具](calculator_agent/README.md) |
| 工具之间怎样传递真实结果 | [天气工具](weather_agent/README.md)、[手写工具循环](manual_tool_loop/README.md)、[框架工具调用](autogen_tool_loop/README.md) |
| 当前输入怎样保留必要事实 | [对话历史](conversation_memory/README.md) |
| 跨会话状态怎样写入与恢复 | [持久记忆](persistent_memory/README.md)、[文件系统记忆](filesystem_memory/README.md) |
| 生成的代码是否真的可用 | [代码转换](code_translation/README.md)、[代码解释器](code_interpreter/README.md) |

这些实验独立运行。一次任务完成后，分别检查工具是否执行、数据是否正确传递、最终结论是否成立；记录消息、文件和外部服务各自持有什么状态。

## 从实验到自己的执行流程

选择一个需要两步工具协作的任务，先写普通 Python 程序和独立结果检查，再把步骤交给模型选择。故意制造一次无效输入，观察错误能否进入下一轮，以及预算能否使失败任务停止。

当任务需要更多工具或跨进程服务时，进入[MCP 工具发现](../chapter9/mcp_tools/README.md)；需要组合权限、状态与恢复时，继续学习[Harness 的组织](../chapter9/README.md)。

## 参考阅读

- [ReAct：协同推理与行动](https://arxiv.org/abs/2210.03629)：沿动作、环境观察与后续决策理解交互循环，对照手写工具调用。
- [MemGPT：将大模型视作操作系统](https://arxiv.org/abs/2310.08560)：理解不同层次的记忆及其调度，与本地持久化实验的读写和加载机制比较。
- [Reflexion：通过语言反馈改进智能体](https://arxiv.org/abs/2303.11366)：理解怎样把任务反馈保存为可复用经验，继续到[反思与改进](../chapter9/reflection/README.md)核对改写质量。
- [ChatDev：用于软件开发的协作智能体](https://arxiv.org/abs/2307.07924)与[MetaGPT：多智能体协作框架](https://arxiv.org/abs/2308.00352)：阅读角色、沟通和流程分工，比较它们与固定工作流、工具循环的组织方式。

[学习地图](../README.md#学习地图) · [模型配置](../README-DEEPSEEK.md#setup)
