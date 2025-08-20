---
layout: default
title: Lesson 3 - Building a Tool-Using Agent
parent: Conversational Intelligence
nav_order: 3
description: "Practical tool-using agent with external API integration"
---

# Lesson 3: Building a Tool-Using Agent
{: .no_toc }

This lesson demonstrates how to build a practical, tool-using agent with an open-source LLM. You will learn to create an agent that can interact with external APIs to retrieve real-time information and answer user queries.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Key Learning Objectives

- **Tool Creation**: Learn how to define custom tools that call external APIs.
- **Agent Initialization**: Understand how to initialize a LangChain agent and equip it with custom tools.
- **Multi-Step Reasoning**: See how an agent can perform a sequence of actions (e.g., fetch a city code, then fetch the weather) to fulfill a request.
- **API Integration**: Gain experience integrating a third-party API (AMAP Weather API) into your application.

---

## File Descriptions

- `multimodal_chat.py`: Implements an agent that can retrieve real-time weather information. The agent first fetches a city's administrative code and then uses that code to query a weather API. **Note**: The filename is a misnomer; this lesson focuses on tool use, not multimodal chat.
- `requirements.txt`: Lists all the necessary Python dependencies for this lesson.

---

## Setup and Execution

1. **Get an API Key**:
   This lesson uses the AMAP Weather API. You will need to get a free API key from the [AMAP Open Platform](https://lbs.amap.com/).

2. **Configure the API Key**:
   Open `multimodal_chat.py` and replace `'YOUR KEY'` with your actual AMAP API key.
   ```python
   # multimodal_chat.py
   AMAP_KEY = 'YOUR KEY'  # Replace with your AMAP application key
   ```

3. **Install Dependencies**:
   Install the required packages using pip.
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Example**:
   Execute the script to see the agent in action.
   ```bash
   python multimodal_chat.py
   ```
   The agent will process the user's question ("What's the weather in Beijing?"), call the necessary tools, and print the result.

---

## Next Steps

After completing this lesson, proceed to [Lesson 4: Tool Augmentation]({{ site.baseurl }}/docs/chapter1/lesson4).
