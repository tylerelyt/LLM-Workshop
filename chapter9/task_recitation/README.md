<a id="lesson-4-attention-recitation-and-goal-focus-management"></a>

# 目标复述与任务管理

本课学习 Manus 引导注意力的策略，在本地任务状态中更新 `todo.md`，再将主目标、当前任务和进度追加到上下文末尾，检查提醒是否对应最新状态。

## 工程任务

任务执行到一半偏离目标，你要检查目标与待办是否仍然进入后续输入。

在 [attention_recitation_demo.py](attention_recitation_demo.py) 中，固定任务状态，只改变复述注入的频率或位置，每轮只改一项。

对照实际组装的内容选择复述频率，不能用构造任务的完成比例推断模型效果。

## 🎯 学习目标

- **注意力机制**，理解大模型注意力分布的特点与局限
- **复述策略**，掌握通过自然语言引导注意力的方法
- **目标维护**，在长期复杂任务中保持目标一致
- **动态规划**，构建可调整的任务分解与执行机制

<a id="-attention-challenges"></a>

## 🧠 注意力面临的挑战

<a id="lost-in-the-middle-problem"></a>

### “中间信息被忽略”的问题

在长上下文或复杂任务中，Agent 容易出现以下情况。

- **偏离主题**，受到中间观察结果干扰
- **遗忘目标**，丢失最初的任务目的
- **决策漂移**，执行路径逐渐偏离原定方向

<a id="long-loop-task-dilemma"></a>

### 长循环任务的困境

Manus 的典型任务可能包含约 50 次工具调用。

- **上下文膨胀**，每次操作都增加上下文长度
- **注意力分散**，关键信息被大量历史内容淹没
- **目标变模糊**，初始目标在长序列中逐渐不再突出

<a id="-manuss-recitation-solution"></a>

## 💡 Manus 的复述方案

<a id="todomd-mechanism"></a>

### todo.md 机制

在复杂任务中维护 `todo.md`，可以观察到以下行为。

- **自动创建**，为复杂任务建立待办文件
- **逐步更新**，随任务进展更新待办列表
- **状态跟踪**，标记已完成与待处理的事项

<a id="attention-manipulation-principle"></a>

### 注意力引导原理

```
Recitation = Push goals into attention focus
           = Avoid "lost in the middle"
           = Maintain goal consistency
```

<a id="-practice-exercises"></a>

## 🛠️ 实践练习

<a id="exercise-1-intelligent-todo-manager"></a>

### 练习一：智能待办管理器

使用现成的 `AttentionRecitationEngine` 创建任务清单。运行 `--demo todo` 后打开输出工作目录里的 `todo.md`，核对完成 `task_01`、`task_02`、`task_03` 后，下一项活动任务是否变为 `task_04`。练习允许修改 `demonstrate_todo_generation` 的任务描述和 `tasks_to_complete`，任务编号保持来自同一次初始化。

<a id="exercise-2-attention-tracker"></a>

### 练习二：注意力跟踪器

检查 `detect_goal_drift` 中英文关键词的匹配结果。固定其他输入，把同一个 `response_plan` 从空字符串改为 `"by the way, quick question, change subject"`，预测分数是否超过 `2`，再与返回的 `patterns` 对照。用含义相似、但没有这些关键词的句子重试，记录规则会漏掉什么。这一结果描述关键词信号，注意力权重需要模型侧工具才能测量。

<a id="exercise-3-adaptive-recitation-engine"></a>

### 练习三：自适应复述引擎

在 `demonstrate_attention_injection` 中保持目标、任务与原始上下文不变，只将 `inject_attention_focus` 的 `include_progress` 从 `True` 改为 `False`。比较追加内容，当前任务和主目标应保留，进度行应消失。再完成当前任务并重新构造提醒，核对其中的任务编号是否随 `todo.md` 一起更新。

<a id="-file-descriptions"></a>

## 📁 文件说明

`attention_recitation_demo.py` 在一个本地脚本中模拟任务清单、目标提醒和目标漂移。

<a id="-core-technologies"></a>

## 🔍 核心技术

<a id="1-dynamic-task-decomposition"></a>

### 1. 动态任务分解

```python
class TaskDecomposer:
    def decompose_goal(self, goal):
        """Break complex goals into executable steps"""

    def update_progress(self, completed_step):
        """Update progress and adjust subsequent steps"""

    def generate_todo(self):
        """Generate current todo.md content"""
```

<a id="2-attention-guidance"></a>

### 2. 注意力引导

```python
class AttentionGuide:
    def inject_goal_reminder(self, context):
        """Inject goal reminder at end of context"""

    def bias_attention(self, current_state):
        """Bias attention distribution through recitation"""
```

<a id="3-progress-visualization"></a>

### 3. 进度可视化

实时显示任务执行状态。

- ✅ 已完成的步骤
- 🔄 正在进行的步骤
- ⏳ 等待处理的步骤
- 🎯 最终目标

<a id="-practical-cases"></a>

## 🚀 应用案例

<a id="case-1-complex-code-refactoring"></a>

### 案例一：复杂代码重构

大型代码库的重构可能包含 50 个步骤。

```markdown
# todo.md
## Code Refactoring Task Progress
- [x] Analyze existing architecture
- [x] Identify target modules for refactoring
- [🔄] Refactor data layer
  - [x] User model refactoring
  - [🔄] Permission model refactoring
  - [ ] Data validation layer
- [ ] Refactor API layer
- [ ] Update test cases
- [ ] Performance verification

🎯 **Final Goal**: Improve system maintainability and performance
```

<a id="case-2-market-research-report"></a>

### 案例二：市场调研报告

跟踪多来源的信息收集和分析。

```markdown
# research_progress.md
## Market Research Progress Tracking
- [x] Competitive analysis
  - [x] Product A feature research
  - [x] Product B pricing strategy
- [🔄] User interviews
  - [x] Prepare interview questions
  - [🔄] Conduct user interviews (3/10 completed)
- [ ] Data analysis and report generation

🎯 **Core Goal**: Provide data support for product positioning
```

<a id="-design-principles"></a>

## 💡 设计原则

> “通过持续重写待办列表，Manus 将目标复述到上下文末尾，使全局计划重新进入模型近期关注的范围，减少复杂任务中的目标丢失。”
> — Manus AI 团队

<a id="the-art-of-recitation"></a>

### 怎样组织复述

1. **控制频率**，过于频繁会干扰决策，间隔过长则可能失去效果
2. **精炼内容**，保持简洁并覆盖关键信息
3. **动态调整**，根据任务进展改变复述策略
4. **自然集成**，将复述融入 Agent 的工作流

<a id="-advanced-techniques"></a>

## 🧪 高阶方法

<a id="multi-level-recitation"></a>

### 多层次复述

- **宏观目标**，项目的最终目的
- **中观计划**，当前阶段的任务
- **微观步骤**，下一项具体行动

<a id="conditional-recitation"></a>

### 条件触发的复述

根据不同条件触发目标提醒。

- **时间触发**，每执行 N 次操作后复述
- **复杂度触发**，遇到复杂决策时复述
- **偏离检测**，检测到目标偏移时强制复述

<a id="-getting-started"></a>

## 🚀 开始运行

从仓库根目录运行本地演示。

```bash
python chapter9/task_recitation/attention_recitation_demo.py --demo all
```

用 `--demo todo`、`--demo injection` 或 `--demo hierarchy` 单独运行一个阶段。对照追加提醒前后的上下文，检查提醒保留了哪个目标，以及下一步要做什么。

每次运行使用独立临时目录，终端的 `Todo file` 显示当前文件路径。完成检查后，只清理该次演示创建的目录。

起点中的任务完成是本地脚本推进，漂移评分来自固定关键词规则。本课不发送模型请求。用下面的同一实现入口复核两项关键行为。

```bash
python - <<'PY'
from tempfile import TemporaryDirectory
from chapter9.task_recitation.attention_recitation_demo import AttentionRecitationEngine

with TemporaryDirectory() as workspace:
    engine = AttentionRecitationEngine(workspace)
    engine.initialize_project("完成支付模块测试", ["整理测试样例", "执行并记录结果"])
    context = "已收集用户关于页面颜色的讨论。"
    before = engine.inject_attention_focus(context, include_progress=True)
    engine.complete_task("task_01", "样例已整理")
    after = engine.inject_attention_focus(context, include_progress=False)
    assert before.startswith(context) and after.startswith(context)
    assert "Task ID: task_01" in before and "Task ID: task_02" in after
    assert "PROGRESS:" in before and "PROGRESS:" not in after
    assert "执行并记录结果" in engine.active_todo_file.read_text()
    print("原始上下文保留，活动任务与文件同步更新，进度开关已生效。")
PY
```

提交 `todo.md` 的前后片段、追加提醒的差异和一组漂移规则的命中与漏报。若要判断复述是否提高模型任务完成率，需要固定模型、任务和预算，分别运行有提醒与无提醒的流程，并检查实际行动和答案。

<a id="-evaluation-metrics"></a>

## 📊 评估指标

- **本地进度**，清单中已标记完成的任务数与总数之比
- **提醒记录**，追加提醒的次数、字符数与对应活动任务
- **规则信号**，关键词匹配分数、命中的类别与提示次数
- **后续模型实验**，比较真实任务完成率、行动偏离和用量。脚本中的 `focus_effectiveness` 是已启动任务的比例，不能代替模型注意力分布

---

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

选一个有多个未完成事项的实际任务，更新一项状态后检查下一轮输入是否仍保留主目标与限制。把提醒接入[完整 Harness](../mcp_harness/README.md)时，核对真实任务进度，避免把重复目标文字当作已经完成工作。

[主题目录](../README.md) · [课程首页](../../README.md)
