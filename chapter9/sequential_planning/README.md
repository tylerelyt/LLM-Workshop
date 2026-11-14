# 顺序工作流

## 工程任务

模型给多个方案打分并排序，看起来有条理，但这些分数未必能支撑实际选型。

在 [sequential_workflow.py](sequential_workflow.py) 中，固定题目与模型，只在评估阶段加入一条明确筛选标准。

检查原始约束是否进入后续评估，指出哪些结论有依据、哪些仍需外部实验。

## 学习目标

将一个问题拆成固定的生成、评估、深化和排序步骤，追踪步骤之间的变量传递。

## 前置条件

使用 Python 3.11 或 3.12。按[模型配置说明](../../README-DEEPSEEK.md#setup)配置服务。聊天请求直接使用课程的 Chat Completions 客户端。 本课独立安装依赖，从仓库根目录运行：

```bash
python -m pip install -r chapter9/sequential_planning/requirements.txt
python chapter9/sequential_planning/sequential_workflow.py
```

## 动手任务

先运行默认问题，程序按阶段显示，并可用 `--output` 保存 `solutions`、`review`、`deepen_thought_process` 与 `ranked_solutions`。将实际文本与四个提示模板对照，标明下一步读取了哪个变量。

固定问题，只更换约束，再运行一次。

```bash
python chapter9/sequential_planning/sequential_workflow.py \
  --constraints '必须保留原文出处；使用公开教学资料；只允许本地部署；本轮不训练模型'
```

运行前先预测约束会怎样影响评估和排序。运行后检查原始约束是否进入每一步、第一步方案是否进入评估、评估是否进入深化、深化是否进入排序。模型给出的成功概率属于方案判断，需与真正测量的数据区分。

## 验收要求

保留两份四步中间结果，标明每步读取与输出的变量。引用具体方案或排序理由解释约束是否被传递，不能只以“输出了四个字段”验收。说明为什么本程序始终执行四步，而 ReAct 可以依据观察选择下一种工具动作。

## 在自己的项目中使用

将一个实际需求拆成可检查的阶段产物，确保每阶段都能看到原始限制。用独立实验核对最终建议；若后续步骤必须根据工具结果动态选择，再对照[Agent Loop](../mcp_harness/README.md)决定控制流由谁管理。

[主题目录](../README.md)
