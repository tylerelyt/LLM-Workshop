---
layout: default
title: Lesson 2 - Tool Masking Strategy and Dynamic Behavior Control
parent: Context Engineering
nav_order: 2
description: "Mask tools instead of removing them to optimize agent behavior"
---

# Lesson 2: Tool Masking Strategy and Dynamic Behavior Control
{: .no_toc }

This lesson is based on Manus's "Mask, Don't Remove" principle, learning how to optimize agent behavior through tool masking rather than removal, avoiding cache invalidation while improving decision quality.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## 🎯 Learning Objectives

- **Tool Masking Principles**: Understand why masking is better than removing tools
- **State Machine Design**: Build context-aware tool availability management
- **Logits Manipulation**: Achieve precise behavior control through token constraints
- **MCP Integration**: Handle challenges of large-scale tool collections

## 🔧 Core Challenges

### Tool Explosion Problem
As agent capabilities expand, tool counts grow dramatically:
- **User Configuration**: Users may insert hundreds of custom tools
- **Decision Confusion**: Too many choices lead agents to select wrong or inefficient paths
- **Performance Degradation**: "Armed to the teeth" agents actually become dumber

### Problems with Traditional Solutions
Dynamic add/remove tools seem reasonable, but have fatal flaws:
1. **Cache Invalidation**: Tool definition changes cause KV-Cache invalidation
2. **Context Confusion**: Historical behavior references deleted tool definitions

## 💡 Manus's Solution

### State Machine + Masking Strategy
- **Keep Tool Definitions**: All tools always defined in context
- **Logits Masking**: Control actual availability through token constraints
- **Prefix Design**: Tool naming uses consistent prefixes for batch control

### Three Function Call Modes
Response pre-filling based on Hermes format:

1. **Auto Mode**: `<|im_start|>assistant`
   - Agent can choose whether to call functions

2. **Required Mode**: `<|im_start|>assistant<tool_call>`
   - Must call function, but selection is unrestricted

3. **Specified Mode**: `<|im_start|>assistant<tool_call>{"name": "browser_`
   - Must select from specific subset of functions

## 🛠️ Practice Exercises

### Exercise 1: Intelligent Tool Manager
Build a management system that can dynamically mask tools based on context.

### Exercise 2: State Machine-Driven Agent
Implement a state machine-based agent behavior control framework.

### Exercise 3: MCP Tool Integration
Handle masking strategies for large-scale MCP tool collections.

## 📁 File Descriptions

- `tool_masker.py`: Core tool masking implementation
- `state_machine.py`: Context-aware state machine
- `logits_processor.py`: Token-level constraint processing
- `mcp_manager.py`: MCP tool integration management

## 🚀 Getting Started

```bash
# Install dependencies
cd chapter4/lesson2
pip install -r requirements.txt

# Run tool masking example
python tool_masker.py

# Test state machine control
python state_machine.py --demo

# MCP integration demo
python mcp_manager.py --tools 100
```

## 💡 Design Principles

> "Don't remove tools, mask them instead. This maintains cache efficiency while avoiding context confusion."
> — Manus AI Team

### Key Implementation Details
- **Prefix Naming**: Consistent prefixes like `browser_*`, `shell_*`
- **Stateless Processors**: Avoid using stateful logits processors
- **Deterministic Masking**: Ensure same context produces same masking results

## 🔍 Advanced Topics

- **Dynamic Prefix Matching**: Implement flexible tool grouping
- **Conditional Masking**: Tool availability based on complex conditions
- **Performance Optimization**: Efficient masking for large-scale tool sets
- **Debugging Techniques**: Visualization of tool masking states

---

## Next Steps

After completing this lesson, proceed to [Lesson 3: Filesystem as Context]({{ site.baseurl }}/docs/chapter4/lesson3).
