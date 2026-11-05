---
layout: default
title: Lesson 4 - Attention Recitation and Goal Focus Management
parent: Context Engineering
nav_order: 4
description: "Guide agent attention through natural language recitation to maintain goal consistency"
---

# Lesson 4: Attention Recitation and Goal Focus Management
{: .no_toc }

This lesson delves into Manus's attention manipulation strategies, learning how to guide agent attention through natural language recitation to avoid deviating from goals in long tasks.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## 🎯 Learning Objectives

- **Attention Mechanisms**: Understand the characteristics and limitations of LLM attention distribution
- **Recitation Strategies**: Master techniques for manipulating attention through natural language
- **Goal Maintenance**: Achieve goal consistency in long-term complex tasks
- **Dynamic Planning**: Build adaptive task decomposition and execution mechanisms

## 🧠 Attention Challenges

### "Lost in the Middle" Problem
In long contexts or complex tasks, agents easily:
- **Deviate from Topic**: Get distracted by intermediate observations
- **Forget Goals**: Lose the original task objective
- **Decision Drift**: Gradually deviate from optimal paths

### Long-Loop Task Dilemma
Manus's typical tasks require about 50 tool calls:
- **Context Inflation**: Each operation increases context length
- **Attention Dilution**: Key information is obscured by large amounts of historical information
- **Goal Ambiguity**: Initial goals become less prominent in long sequences

## 💡 Manus's Recitation Solution

### Todo.md Mechanism
You may notice Manus's interesting behavior:
- **Auto Creation**: Automatically creates `todo.md` file for complex tasks
- **Progressive Updates**: Updates todo list in real-time as tasks progress
- **Status Tracking**: Marks completed and pending items

### Attention Manipulation Principle
```
Recitation = Push goals into attention focus
           = Avoid "lost in the middle"
           = Maintain goal consistency
```

## 🛠️ Practice Exercises

### Exercise 1: Intelligent Todo Manager
Build a system that can automatically generate and maintain task lists.

### Exercise 2: Attention Tracker
Implement tools for monitoring and analyzing agent attention distribution.

### Exercise 3: Adaptive Recitation Engine
Develop mechanisms that adjust recitation frequency based on task complexity.

## 📁 File Descriptions

- `attention_manager.py`: Core attention management components
- `todo_generator.py`: Intelligent task list generator
- `recitation_engine.py`: Recitation mechanism implementation
- `goal_tracker.py`: Goal consistency monitoring tools

## 🔍 Core Technologies

### 1. Dynamic Task Decomposition
```python
class TaskDecomposer:
    def decompose_goal(self, goal):
        """Break complex goals into executable steps"""
        
    def update_progress(self, completed_step):
        """Update progress and adjust subsequent steps"""
        
    def generate_todo(self):
        """Generate current todo.md content"""
```

### 2. Attention Guidance
```python
class AttentionGuide:
    def inject_goal_reminder(self, context):
        """Inject goal reminder at end of context"""
        
    def bias_attention(self, current_state):
        """Bias attention distribution through recitation"""
```

### 3. Progress Visualization
Real-time display of task execution status:
- ✅ Completed steps
- 🔄 Steps in progress
- ⏳ Pending steps
- 🎯 Final goal

## 🚀 Practical Cases

### Case 1: Complex Code Refactoring
Large codebase refactoring task with 50 steps:
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

### Case 2: Market Research Report
Multi-source information collection and analysis:
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

## 💡 Design Principles

> "By constantly rewriting the todo list, Manus recites goals to the end of the context, pushing the global plan into the model's recent attention range, avoiding getting lost in complex tasks."
> — Manus AI Team

### The Art of Recitation
1. **Frequency Control**: Too frequent interferes with decisions, too infrequent loses effectiveness
2. **Content Refinement**: Recitation content should be concise but include key information
3. **Dynamic Adjustment**: Adjust recitation strategy based on task progress
4. **Natural Integration**: Recitation should naturally integrate into agent workflow

## 🧪 Advanced Techniques

### Multi-Level Recitation
- **Macro Goals**: Project final objectives
- **Meso Plans**: Current phase tasks
- **Micro Steps**: Next specific action

### Conditional Recitation
Trigger recitation based on different conditions:
- **Time Trigger**: Recite after every N operations
- **Complexity Trigger**: Recite when complex decisions are detected
- **Deviation Detection**: Force recitation when goal deviation is detected

## 🚀 Getting Started

```bash
# Install dependencies
cd chapter4/lesson4
pip install -r requirements.txt

# Run attention management demo
python attention_manager.py --demo

# Test Todo generator
python todo_generator.py --task "Complex project planning"

# Analyze attention distribution
python goal_tracker.py --analyze
```

## 📊 Evaluation Metrics

- **Goal Consistency**: Deviation degree of task execution from initial goals
- **Completion Rate**: Success completion proportion of complex multi-step tasks
- **Efficiency Improvement**: Task efficiency improvement from recitation mechanism
- **Attention Focus**: Weight of key information in attention distribution

---

## Next Steps

After completing this lesson, proceed to [Lesson 5: Error Preservation and Failure Learning]({{ site.baseurl }}/docs/chapter4/lesson5).
