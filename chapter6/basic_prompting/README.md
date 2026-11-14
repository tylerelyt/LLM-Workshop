<a id="lesson-5-basic-prompting-techniques"></a>

# 基础提示方法

本课介绍与大模型交互的基础提示技巧，对照零样本与少样本提示，并观察它们在具体任务中的用法。

## 工程任务

分类结果不稳定时，你需要判断少量示例是否能改善同一个任务的输出。

在 [example1.py](example1.py) 中，固定 example1.py 的评论与模型，只改变是否提供两个示例。

根据同一评论的两份提示和实际分类，决定保留哪些示例；一次命中不能说明所有评论都有效。

## 学习目标

- **少样本提示**：在提示中提供示例，引导模型输出。
- **零样本提示**：直接描述任务，让模型在没有示例的情况下完成它。

---

<a id="file-descriptions"></a>

## 文件说明

- `example1.py`：通过正面与负面示例，引导模型完成情感分析。
- `example2.py`：用零样本提示，让模型解释一个复杂主题。
- `requirements.txt`：列出本课所需的 Python 依赖。

---

<a id="setup-and-execution"></a>

## 环境准备与运行

按[模型配置](../../README-DEEPSEEK.md#setup)设置 `OPENAI_BASE_URL`、`OPENAI_MODEL` 和 `OPENAI_API_KEY`，然后从仓库根目录运行两个示例。[模型配置](../../README-DEEPSEEK.md#setup)

```bash
python -m pip install -r chapter6/basic_prompting/requirements.txt
python chapter6/basic_prompting/example1.py
python chapter6/basic_prompting/example2.py
```

先对照同一句评论，只改变提示中是否包含两个示例。

```bash
python chapter6/basic_prompting/example1.py --zero-shot
python chapter6/basic_prompting/example1.py
```

两次都使用同一模型和评论“我对这部电影感到失望”。程序打印示例数及实际提示，再打印分类结果。先预测移除示例会改变哪部分输入，保留两次输出，并核对标签是否符合评论。若结果相同，记录“本次分类未变化”，继续解释提示中示例的作用，不能仅凭一题判断整体准确率。

`example2.py` 是独立的零样本解释任务。在其中只改变解释面向的读者，例如增加“小学生也能理解”，再核对输出是否围绕同一主题并采用合适表达。两项任务分别按分类是否正确、解释是否符合受众要求验收。

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

选择一组包含正常、边界与含糊输入的问题，先定义怎样判断输出合格，再固定题目比较提示。需要外部事实时，继续做[向量问答](../vector_qa/README.md)，检查提示改进与补充证据分别解决了什么。

[主题目录](../README.md) · [课程首页](../../README.md)
