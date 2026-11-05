---
layout: default
title: Lesson 5 - Error Preservation and Failure Learning
parent: Context Engineering
nav_order: 5
description: "Preserve errors instead of hiding them to enable agent learning from failures"
---

# Lesson 5: Error Preservation and Failure Learning
{: .no_toc }

This lesson explores Manus's counterintuitive perspective: don't hide errors, preserve them. Learn how to make agents learn from failures, turning errors into opportunities for improvement.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## 🎯 Learning Objectives

- **Error Values**: Understand the positive role of errors in agent learning
- **Context Preservation**: Master effective strategies for preserving error information
- **Adaptive Learning**: Implement dynamic behavior adjustment based on errors
- **Recovery Mechanisms**: Build elegant error recovery and retry systems

## ❌ Misconceptions in Traditional Error Handling

### Common "Cleanup" Impulses
Developers typically tend to:
- **Hide Errors**: Clean error traces, only keep successful paths
- **Reset State**: Reset model state on errors, "start fresh"
- **Fuzzy Handling**: Rely on "magical temperature" to solve problems

### Costs of Hiding Errors
This approach seems safer and more controllable, but actually:
- **Lost Evidence**: Error traces contain valuable learning information
- **Repeat Mistakes**: Without evidence, agents cannot avoid repeating errors
- **Poor Adaptability**: Lose self-correction capabilities

## 💡 Manus's Error Preservation Philosophy

### Core Philosophy
> "Errors are not bugs, they're features. Error recovery is the clearest indicator of true agent behavior."

### Preservation Strategy
1. **Complete Preservation**: Preserve failed actions and corresponding observations
2. **Context Learning**: Let models see errors and their consequences
3. **Implicit Updates**: Implicitly update model beliefs through error evidence
4. **Prior Shift**: Reduce probability of repeating similar errors

## 🛠️ Practice Exercises

### Exercise 1: Error Trace Analyzer
Build tools for analyzing and visualizing agent error patterns.

### Exercise 2: Adaptive Retry Mechanism
Implement intelligent retry systems that can learn from errors.

### Exercise 3: Error Recovery Evaluation
Develop benchmarks for evaluating agent error recovery capabilities.

## 📁 File Descriptions

- `error_tracker.py`: Error trace recording and analysis
- `recovery_engine.py`: Error recovery mechanism implementation
- `failure_learner.py`: Core logic for learning from failures
- `adaptive_retry.py`: Adaptive retry strategies

## 🔍 Error Type Analysis

### 1. Environment Errors
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

### 2. Logic Errors
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

### 3. Semantic Errors
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

## 🧠 Learning Mechanism Principles

### Implicit Belief Updates
When agents see errors:
```
Prior(Action_Similar) = High
After seeing Error:
Posterior(Action_Similar) = Lower
```

### Error Pattern Recognition
Agents learn to identify patterns that lead to errors:
- **Parameter Combinations**: Which parameter combinations are error-prone
- **Environment States**: What states are prone to failure
- **Temporal Dependencies**: Timing requirements of certain operations

## 🚀 Practical Cases

### Case 1: File Operation Error Learning
```python
# First attempt
action_1 = {"tool": "file_read", "path": "/nonexistent/file.txt"}
observation_1 = {"error": "FileNotFoundError", "path": "/nonexistent/file.txt"}

# Agent sees this error in context, learns to check file existence first
action_2 = {"tool": "file_exists", "path": "/target/file.txt"}
observation_2 = {"exists": true}

action_3 = {"tool": "file_read", "path": "/target/file.txt"}
observation_3 = {"content": "file content...", "success": true}
```

### Case 2: API Retry Strategy Learning
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

## 💡 Design Principles

### 1. Preserve but Structure
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

### 2. Maintain Diversity
Avoid agents getting stuck in error pattern solidification:
```python
def add_diversity(self, context):
    """Add diversity to error context"""
    # Different error description methods
    # Randomize some non-critical details
    # Keep core error information unchanged
```

## 🔬 Advanced Strategies

### Error Classification Learning
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

### Recovery Strategy Optimization
```python
class RecoveryOptimizer:
    def suggest_recovery(self, error, history):
        """Suggest recovery strategy based on historical errors"""
        similar_errors = self.find_similar(error, history)
        successful_recoveries = [e for e in similar_errors if e.recovered]
        return self.recommend_strategy(successful_recoveries)
```

## 📊 Evaluation Metrics

- **Error Recovery Rate**: Proportion of successful recoveries from errors
- **Repeat Error Reduction**: Declining trend of same errors repeating
- **Adaptation Time**: Time for agent to learn avoiding specific errors
- **Recovery Efficiency**: Average steps required for error recovery

## 🚀 Getting Started

```bash
# Install dependencies
cd chapter4/lesson5
pip install -r requirements.txt

# Run error analysis demo
python error_tracker.py --analyze

# Test recovery mechanism
python recovery_engine.py --test-scenarios

# Evaluate learning effectiveness
python failure_learner.py --benchmark
```

## 🎯 Key Insights

> "In multi-step tasks, failure is not an exception, but the norm. Language models hallucinate, environments return errors, external tools fail, unexpected edge cases always appear. Hiding these failures removes evidence, and without evidence, models cannot adapt."
> — Manus AI Team

The strongest agents are not those that never make mistakes, but those that can gracefully recover, learn from errors, and continuously improve.

---

## Next Steps

After completing Chapter 4, proceed to [Chapter 5: Multimodal Models]({{ site.baseurl }}/docs/chapter5).
