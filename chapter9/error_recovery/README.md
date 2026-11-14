<a id="lesson-5-error-preservation-and-failure-learning"></a>

# 错误保留与失败学习

本课学习 Manus 保留错误的思路，通过本地脚本保存失败证据、比较恢复策略，并验证重试预算怎样影响同一固定故障的结果。错误跟踪器使用构造记录，恢复引擎使用模拟结果，失败学习器按规则生成建议；自适应重试会实际调用传入的 Python 函数。

## 工程任务

调用失败后不断重试可能浪费时间，也可能掩盖不可恢复的错误。

在 [adaptive_retry.py](adaptive_retry.py) 中，固定一个失败场景，只改变重试次数上限，保持错误记录。

根据保留的失败、尝试次数和终止原因，区分值得重试与应停止处理的情况。

## 🎯 学习目标

- **错误的价值**，理解错误对 Agent 学习的作用
- **上下文保留**，掌握保存错误信息的方法
- **自适应学习**，根据错误动态调整行为
- **恢复机制**，构建错误恢复与重试系统

<a id="-misconceptions-in-traditional-error-handling"></a>

## ❌ 传统错误处理中的误区

<a id="common-cleanup-impulses"></a>

### 常见的“清理”做法

开发中经常出现以下处理方式。

- **隐藏错误**，清理失败轨迹，只留下成功路径
- **重置状态**，发生错误后清空模型状态并重新开始
- **模糊处理**，仅靠调整 temperature 寄希望于模型自行解决问题

<a id="costs-of-hiding-errors"></a>

### 隐藏错误的代价

上述做法会影响 Agent 后续的判断。

- **证据丢失**，错误轨迹中可用于学习的信息被删除
- **重复犯错**，缺少证据时，Agent 难以避免相同错误
- **适应能力下降**，失去自我修正所需的信息

<a id="-manuss-error-preservation-philosophy"></a>

## 💡 Manus 的错误保留理念

<a id="core-philosophy"></a>

### 核心理念

> “错误是系统行为的一部分。错误恢复能力最能体现 Agent 的实际表现。”

<a id="preservation-strategy"></a>

### 保留策略

1. **完整保存**，保留失败动作及其对应的观察结果
2. **上下文学习**，让模型看到错误与后果
3. **隐式更新**，通过错误证据调整模型后续判断
4. **调整先验**，降低再次选择类似错误动作的概率

<a id="-practice-exercises"></a>

## 🛠️ 实践练习

<a id="exercise-1-error-trace-analyzer"></a>

### 练习一：错误轨迹分析器

先运行 `error_tracker.py --create-demo`，再用新的进程运行 `error_tracker.py --analyze`。打开 `demo_error_history.json`，将一次失败动作的参数、错误码、恢复动作和 `resolved` 串起来。这组教学数据包含四个错误及预先标记的成功恢复记录。

只修改 `create_demo_scenarios()` 中限速场景的恢复结果，将对应 `track_recovery` 调用的 `success=True` 改成 `False`，然后在一个新目录重新生成数据。先预测整体恢复率和 `wait_retry` 的成功率，再检查是否分别从 `4/4` 变为 `3/4`、从 `1/1` 变为 `0/1`。四条原始失败记录都应保留。恢复标记属于本地构造数据，要解释这些比例的分母。

<a id="exercise-2-adaptive-retry-mechanism"></a>

### 练习二：自适应重试机制

运行 `adaptive_retry.py --benchmark`，观察一个固定函数在前两次调用抛出 `ConnectionError`、第三次才返回成功。首轮最多尝试两次，应失败；学习器把下一轮预算调到三次，重置故障函数后再运行，应在第三次成功。比较两次会话的 `config.max_attempts`、`attempts` 和 `final_success`，核对旧会话的预算仍为二。

在 `AdaptiveRetry._update_learned_config()` 中找到失败后增加预算的规则。先预测将这项规则改成维持原预算会怎样，再修改并重跑同一基准。行为检查应报错，恢复原规则后再通过。保留两次输出，说明结果差异来自哪次函数调用。

运行 `--demo` 后，在同一工作目录用新的进程运行 `--analyze`。会话与学习配置保存在 `adaptive_retry_history.retries.json`，失败尝试保留 `error_code` 和 `error_message`。检查 `planned_delay` 与 `delay_used`：前者是策略算出的等待时间，后者是演示实际请求的等待时间，每次最多两秒。基准包含策略等待三秒、演示等待两秒的检查。

<a id="exercise-3-error-recovery-evaluation"></a>

### 练习三：错误恢复评估

运行 `failure_learner.py --benchmark`，先检查固定的十六条错误及三个预期结果。文件读取和 API 错误各占 `5/16`，应形成两条高频错误提示；所有参数值不同，因此问题参数提示为零；前八条错误集中出现，应识别时间突发。

只把 `_analyze_frequent_failures()` 的错误占比门槛从 `0.3` 改成 `0.35`，先预测哪项检查会失败，再运行并解释。保持基准中的输入和预期数量不变，观察检测规则对结果的影响，最后恢复门槛。本方法统计某类工具占全部已记录错误的比例，计算工具操作失败率还需要成功操作的数量。

对照 `recovery_engine.py` 的策略选择规则：当前错误之外，一小时内已有超过五条同签名历史失败且没有成功恢复经验时，会选择跳过。检查返回值的 `success=False`、`skipped=True`，以及保存的错误记录中的 `resolved=False`，原任务仍待处理。历史策略效果按每种策略的成功尝试数除以该策略全部尝试数计算。恢复引擎中的操作结果由随机教学函数产生，模型看到错误后改变决策的效果需要另行用真实 Agent 轨迹核对。

<a id="-file-descriptions"></a>

## 📁 文件说明

- `error_tracker.py` 负责错误轨迹的记录与分析
- `recovery_engine.py` 实现错误恢复机制
- `failure_learner.py` 实现从失败中学习的核心逻辑
- `adaptive_retry.py` 演示自适应重试策略

<a id="-error-type-analysis"></a>

## 🔍 错误类型分析

<a id="1-environment-errors"></a>

### 1. 环境错误

```python
# Example: API call failure
action = {"tool": "api_call", "endpoint": "/users"}
observation = {
    "error": "ConnectionTimeout",
    "message": "Request timed out after 30s",
    "timestamp": "2025-07-20T10:30:00Z"
}
# Preserve this error, let agent learn to handle network issues
```

<a id="2-logic-errors"></a>

### 2. 逻辑错误

```python
# Example: Wrong parameter selection
action = {"tool": "calculator", "operation": "divide", "a": 10, "b": 0}
observation = {
    "error": "ZeroDivisionError",
    "message": "division by zero",
    "stack_trace": "..."
}
# Preserve this error, let agent learn parameter validation
```

<a id="3-semantic-errors"></a>

### 3. 语义错误

```python
# Example: Misunderstanding task requirements
action = {"tool": "file_write", "path": "/tmp/summary.txt", "content": "detailed analysis..."}
observation = {
    "error": "TaskMismatchError",
    "message": "Expected summary but got detailed analysis",
    "expected_length": "< 100 words",
    "actual_length": "500 words"
}
# Preserve this error, let agent learn task understanding
```

<a id="-learning-mechanism-principles"></a>

## 🧠 学习机制

<a id="implicit-belief-updates"></a>

### 隐式更新判断

Agent 看到错误后，可以据此调整对类似动作的判断。

```
Prior(Action_Similar) = High
After seeing Error:
Posterior(Action_Similar) = Lower
```

<a id="error-pattern-recognition"></a>

### 错误模式识别

Agent 从错误证据中识别容易导致失败的模式。

- **参数组合**，哪些组合容易出错
- **环境状态**，什么状态下容易失败
- **时序依赖**，某些操作对执行时机有什么要求

<a id="-practical-cases"></a>

## 🚀 应用案例

<a id="case-1-file-operation-error-learning"></a>

### 案例一：文件操作错误学习

```python
# First attempt
action_1 = {"tool": "file_read", "path": "/nonexistent/file.txt"}
observation_1 = {"error": "FileNotFoundError", "path": "/nonexistent/file.txt"}

# Agent sees this error in context, learns to check file existence first
action_2 = {"tool": "file_exists", "path": "/target/file.txt"}
observation_2 = {"exists": True}

action_3 = {"tool": "file_read", "path": "/target/file.txt"}
observation_3 = {"content": "file content...", "success": True}
```

<a id="case-2-api-retry-strategy-learning"></a>

### 案例二：API 重试策略学习

```python
# Preserved error history helps agent learn exponential backoff
errors_seen = [
    {"attempt": 1, "error": "RateLimit", "retry_after": 1},
    {"attempt": 2, "error": "RateLimit", "retry_after": 2},
    {"attempt": 3, "error": "RateLimit", "retry_after": 4}
]

# Agent learns smarter retry strategy
action_next = {
    "tool": "wait",
    "duration": 8,  # Learned exponential backoff
    "reason": "Rate limit pattern detected"
}
```

<a id="-design-principles"></a>

## 💡 设计原则

<a id="1-preserve-but-structure"></a>

### 1. 结构化保存错误

```python
class ErrorContext:
    def __init__(self):
        self.error_history = []
        self.success_patterns = []
        self.failure_patterns = []

    def add_error(self, action, error, context):
        """Structurally save error information"""
        error_record = {
            "action": action,
            "error": error,
            "context": context,
            "timestamp": now(),
            "recovery_attempts": []
        }
        self.error_history.append(error_record)
```

<a id="2-maintain-diversity"></a>

### 2. 保持多样性

避免 Agent 的错误模式逐渐固化。

```python
def add_diversity(self, context):
    """Add diversity to error context"""
    # Different error description methods
    # Randomize some non-critical details
    # Keep core error information unchanged
```

<a id="-advanced-strategies"></a>

## 🔬 高阶策略

<a id="error-classification-learning"></a>

### 错误分类学习

```python
class ErrorClassifier:
    def classify_error(self, error):
        """Classify error types for targeted learning"""
        return {
            "type": "transient|permanent|configuration",
            "severity": "low|medium|high|critical",
            "recovery_strategy": "retry|skip|alternative|abort"
        }
```

<a id="recovery-strategy-optimization"></a>

### 恢复策略优化

```python
class RecoveryOptimizer:
    def suggest_recovery(self, error, history):
        """Suggest recovery strategy based on historical errors"""
        similar_errors = self.find_similar(error, history)
        successful_recoveries = [e for e in similar_errors if e.recovered]
        return self.recommend_strategy(successful_recoveries)
```

<a id="-evaluation-metrics"></a>

## 📊 评估指标

- **错误恢复率**，已解决错误数除以全部错误数，跳过原任务应保留为未解决
- **策略成功率**，某种策略的成功尝试数除以该策略全部尝试数
- **错误占比**，某工具的错误数除以全部已记录错误数，见失败学习器的 `supporting_evidence`
- **重复错误减少量**，在可比较的重复任务中统计同类错误，比较改策略前后是否下降
- **适应时间**，记录固定任务从失败到调整策略并恢复所需的轮次和耗时
- **恢复效率**，对照重试会话中的尝试次数、实际等待与 `total_duration`。恢复引擎的 `average_recovery_time` 目前为占位数据，不能据此报告实际恢复耗时

<a id="-getting-started"></a>

## 🚀 开始运行

从仓库根目录安装依赖，并在一个新目录中运行。保留 `workshop_out`，便于打开本次结果。各脚本使用的数据文件如下。

| 入口 | 读取与保存的证据 |
|---|---|
| `error_tracker.py` | `demo_error_history.json` 中的构造错误和恢复记录 |
| `failure_learner.py --analyze` | 读取 `demo_error_history.json`，写出 `learning_insights.json` |
| `recovery_engine.py` | 独立的 `recovery_test_history.json`，保存模拟策略与结果 |
| `adaptive_retry.py` | `adaptive_retry_history.retries.json`，保存实际函数调用的重试会话和下一轮配置 |

```bash
python -m pip install -r chapter9/error_recovery/requirements.txt
lesson5_dir="$PWD/chapter9/error_recovery"
workshop_out="$(mktemp -d)"
(
  cd "$workshop_out" || exit 1
  python "$lesson5_dir/error_tracker.py" --create-demo
  python "$lesson5_dir/error_tracker.py" --analyze
  python "$lesson5_dir/failure_learner.py" --analyze
  python "$lesson5_dir/recovery_engine.py" --test-scenarios
  python "$lesson5_dir/recovery_engine.py" --analyze
  python "$lesson5_dir/adaptive_retry.py" --demo
  python "$lesson5_dir/adaptive_retry.py" --analyze
)
python "$lesson5_dir/failure_learner.py" --benchmark
python "$lesson5_dir/adaptive_retry.py" --benchmark
```

将保存的错误证据与恢复动作、学习器的建议逐条对照。两项基准使用临时的固定数据并自行清理；`--demo` 的随机结果用于练习读取轨迹，比较优化效果时使用相同的固定故障。重跑时选择新目录作为基线，验证持久化时保留原目录并启动新进程。

<a id="-key-insights"></a>

## 🎯 关键认识

> “多步任务中经常发生失败。语言模型可能产生幻觉，环境可能报错，外部工具可能失败，也可能遇到未预期的边界情况。保留这些失败才能让模型看到证据，并据此调整行为。”
> — Manus AI 团队

Agent 应能够从错误中恢复、利用失败证据学习，并持续改进后续表现。

---

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

为自己的工具区分暂时失败、输入错误和权限不足，设定停止与重试条件，再构造固定故障观察实际次数。接入[工具循环](../../chapter8/manual_tool_loop/README.md)后，检查错误是否进入下一轮，以及恢复有没有重复执行已成功的动作。

[主题目录](../README.md) · [课程首页](../../README.md)
