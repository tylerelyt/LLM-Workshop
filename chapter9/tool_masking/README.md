<a id="lesson-2-tool-masking-strategy-and-dynamic-behavior-control"></a>

# 工具遮罩与动态行为控制

本课基于 Manus 的“保留工具定义，通过遮罩控制可用性”原则，用本地状态规则限制可以进入执行器的工具名称，并检查切换状态时完整工具定义是否保持一致。

## 工程任务

同一个工具在不同任务状态下应有不同权限。模型提议了动作，运行程序仍要执行约束。

在 [tool_masking_demo.py](tool_masking_demo.py) 中，固定提议的工具，只改变 --state，观察本地选择守卫。

用本地守卫的实际允许与拒绝结果解释边界，说明哪些结论还需要在线服务验证。

## 🎯 学习目标

- **工具遮罩原理**，理解遮罩与删除工具对上下文的不同影响
- **状态机设计**，根据当前上下文管理工具可用性
- **解码约束接入点**，区分本地选择守卫与推理后端执行的 token 约束
- **MCP 集成**，应对大规模工具集合带来的挑战

<a id="-core-challenges"></a>

## 🔧 核心挑战

<a id="tool-explosion-problem"></a>

### 工具数量膨胀

随着 Agent 能力扩展，工具数量可能大幅增加。

- **用户配置**可能一次引入数百个自定义工具
- **选择困难**会使 Agent 走向错误或低效的执行路径
- **性能下降**可能发生在工具配置过多时

<a id="problems-with-traditional-solutions"></a>

### 动态增删工具的问题

动态添加和移除工具会带来两类影响。

1. **缓存失效**，工具定义变化可能使 KV-Cache 无法复用
2. **上下文不一致**，历史行为可能仍引用已删除的工具定义

<a id="-manuss-solution"></a>

## 💡 Manus 的解决方法

<a id="state-machine--masking-strategy"></a>

### 状态机与遮罩策略

- **保留工具定义**，让上下文中始终包含完整定义
- **logits 遮罩**，通过 token 约束控制实际可用性
- **前缀设计**，使用一致的工具命名前缀，便于按组控制

<a id="three-function-call-modes"></a>

### 三种函数调用模式

基于 Hermes 格式预填响应。

1. **自动模式**，预填 `<|im_start|>assistant`
   - Agent 自行决定是否调用函数

2. **必须调用模式**，预填 `<|im_start|>assistant<tool_call>`
   - 必须调用函数，可以自由选择具体函数

3. **指定范围模式**，预填 `<|im_start|>assistant<tool_call>{"name": "browser_`
   - 必须从指定的函数子集中选择

<a id="-getting-started"></a>

## 🚀 开始运行

从仓库根目录运行本地模拟。

```bash
python chapter9/tool_masking/tool_masking_demo.py --demo all
```

用 `--demo transitions`、`--demo analysis` 或 `--demo pollution` 单独运行一部分。起点注册了 19 个教学工具定义，`get_available_tools` 返回全部定义及每项的 `enabled` 状态。`pollution` 对照检查完整定义保持一致，再把候选工具送入同一个选择守卫。程序打印的名称前缀片段用于说明解码约束的接入位置，本地流程只执行规则选择。

### 固定候选工具，只改变状态

先预测 `shell_execute` 在下面两个状态中是否允许，再运行同一个入口。

```bash
python chapter9/tool_masking/tool_masking_demo.py --demo selection \
  --state file_operations --tool shell_execute
python chapter9/tool_masking/tool_masking_demo.py --demo selection \
  --state system_admin --tool shell_execute
```

第一条应报告选择被拒绝，第二条应允许交给执行器。这里检查的是候选名称的准入，工具描述中的文件、Shell 和消息操作均作为教学定义保留。

在 `_define_masking_rules` 中只修改 `SYSTEM_ADMIN` 的 `blocked_prefixes`，加入 `shell_`，重跑第二条命令。即使 `allowed_prefixes` 仍含有 `shell_`，阻止规则也应生效。恢复规则后再运行 `--demo pollution`，记录定义长度、允许列表和 `file_read`、`shell_execute` 两次选择结果。

提交状态规则改动前后的同一候选结果，以及完整定义未变化的检查。缓存命中、模型选择准确率和实际 logits 遮罩效果，需要在接入推理后端后使用相同任务另行测量。

<a id="-practice-extensions"></a>

## 🛠️ 扩展练习

向 `tool_masking_demo.py` 添加一个状态或工具前缀，重新运行状态切换演示，检查新的允许列表与选择守卫是否一致。本部分的 MCP 工具练习将工具发现用于实际运行的 MCP 服务。[MCP 练习](../mcp_tools/README.md)

<a id="-design-principles"></a>

## 💡 设计原则

> “保留工具定义，通过遮罩限制可用性，从而兼顾缓存复用与上下文一致性。”
> — Manus AI 团队

<a id="key-implementation-details"></a>

### 实现要点

- **前缀命名**保持一致，例如 `browser_*`、`shell_*`
- **无状态处理器**避免依赖带有隐含状态的 logits 处理器
- **确定性遮罩**保证相同上下文产生相同的遮罩结果

<a id="-advanced-topics"></a>

## 🔍 高阶主题

- **动态前缀匹配**，灵活组织工具分组
- **条件遮罩**，根据复杂条件控制工具可用性
- **性能优化**，提高大规模工具集合的遮罩效率
- **调试方法**，将工具遮罩状态可视化

---

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

为自己的工具流程定义各状态允许的动作，在执行入口检查权限，再让模型提出一次越界动作。将同一限制接入[完整 Harness](../mcp_harness/README.md)，观察模型建议、程序拒绝与后续恢复是否形成闭环。

[主题目录](../README.md) · [课程首页](../../README.md)
