---
layout: default
title: Lesson 3 - Implementing a ReAct Agent
parent: Advanced Reasoning
nav_order: 3
description: "ReAct framework implementation from scratch"
---

# Lesson 3: Implementing a ReAct Agent
{: .no_toc }

This lesson provides a deep dive into the ReAct (Reason, Act) framework, a powerful paradigm for building agents that can reason about a problem, use tools to gather information, and formulate a final answer. You will learn how to implement a ReAct agent from scratch.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Key Learning Objectives

- **ReAct Framework**: Understand the core "Thought -> Action -> Observation" loop that powers ReAct agents.
- **Tool Creation and Registration**: Learn how to create a registry for custom tools that the agent can use.
- **Dynamic Prompting**: See how to construct a detailed system prompt that instructs the LLM on how to behave as a ReAct agent, including the available tools and the expected output format.
- **Agent Loop**: Implement the main control loop that parses the LLM's output, executes actions, and feeds observations back into the context.

---

## File Descriptions

- `example1.py`: A complete, from-scratch implementation of a ReAct agent. The agent is tasked with solving a problem that requires both looking up scientific constants and performing calculations. The code clearly demonstrates the tool registry, dynamic prompt generation, and the main reasoning loop.
- `requirements.txt`: Lists all the necessary Python dependencies for this lesson.

---

## Setup and Execution

1. **Install Dependencies**:
   Install the required packages using pip.
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Example**:
   Execute the script to see the ReAct agent solve the problem step-by-step.
   ```bash
   python example1.py
   ```
   The script will output the agent's internal monologue (Thought), the actions it takes, the observations it makes from the tools, and the final answer.

---

## Next Steps

After completing Chapter 2, proceed to [Chapter 3: Retrieval & Knowledge Engineering]({{ site.baseurl }}/docs/chapter3).
