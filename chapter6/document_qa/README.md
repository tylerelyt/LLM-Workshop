<a id="lesson-2-document-processing"></a>

# 文档提取与问答

学习目标是解释读取范围如何影响答案：从文档提取可引用的原文，再验证模型能否把答案落回原文。练习支持 UTF-8 的 TXT、Markdown 和有文本层的 PDF。

## 工程任务

文档问答只读取部分页面时，模型可能缺少决定性条款。

在 [document_processing.py](document_processing.py) 中，固定文档、问题和模型，只改变 --max-pages。

指出回答所需的具体页码，解释读取范围与证据缺口，而不是按答案长度评价。

## 环境准备

使用课程的 Python 3.11 或 3.12 环境，在仓库根目录安装本课依赖，并为问答步骤配置聊天模型。[模型配置](../../README-DEEPSEEK.md)

```bash
python -m pip install -r chapter6/document_qa/requirements.txt
```

<a id="extract-then-ask"></a>

## 先提取，再提问

从仓库根目录运行第一条命令，先查看原文及页码。第二条命令让模型回答同一个文档里的问题。

```bash
python -m chapter6.document_qa.document_processing chapter6/document_qa/sample.txt
python -m chapter6.document_qa.document_processing chapter6/document_qa/sample.txt \
  --question '发布前由谁审批？文档给了电话号码吗？'
```

样例是两页教学构造资料。第 1 页说明发布审批，第 2 页说明回滚与联系方式缺失。程序先打印本次真正传给模型的片段，再打印答案。核对审批规则所在的原文与答案的 `[页 N]` 引用，检查模型怎样处理文档没有提供的电话号码。

## 只改变读取页数

固定文档、模型和问题，先预测只读第一页会缺少哪条依据，再对照两次运行。

```bash
QUESTION='发布前由谁审批？由谁发起回滚？请分别引用页码。审批人的电话号码是多少？'
python -m chapter6.document_qa.document_processing chapter6/document_qa/sample.txt --max-pages 1 --question "$QUESTION"
python -m chapter6.document_qa.document_processing chapter6/document_qa/sample.txt --max-pages 2 --question "$QUESTION"
```

学员本轮只改 `--max-pages`。第一轮应能回答审批问题，并说明缺少回滚依据。第二轮应增加第 2 页的回滚依据，两轮都不能推断电话号码。每次都是独立请求，不沿用前一轮答案。

<a id="process-a-pdf"></a>

## 处理 PDF

处理有文本层的 PDF 时，将样例路径换成自己的文档路径。`pypdf` 会逐页提取文字。用 `--max-pages` 选择读取前 1—20 页，默认读取前 5 页。

```bash
PDF_PATH='/absolute/path/to/your-document.pdf'
python -m chapter6.document_qa.document_processing "$PDF_PATH" --max-pages 3
python -m chapter6.document_qa.document_processing "$PDF_PATH" --max-pages 3 \
  --question 'What rule does this document establish, and which page supports it?'
```

扫描版 PDF 需要先提取 OCR 文本，再进入同一练习。TXT 和 Markdown 中的换页符 `\f` 也会分成编号的页面。程序显示实际读取的页数及有文本的页数，检查这些信息后再评估回答。

<a id="practice-and-acceptance"></a>

## 练习与验收

1. 保留两轮同题问答、带编号的实际输入片段和答案。
2. 将审批、回滚、电话三项分别标为有原文支撑或缺少依据。核对页码真实存在、对应文字足以支持结论。
3. 尝试一份有文本层的 PDF，提出需要结合两页信息的问题，并核对两处引用。
4. 记录提取过程是否保留了回答所需的文字。重要证据来自视觉内容时，使用多模态图像练习的图片/OCR 对照方式检查。

文档版式分析和结构化提取可以从这套流程继续扩展。从带编号的片段开始，先对照原文核对提取字段，再增加后续处理。

## 在自己的项目中使用

换入自己的小型文档，为每个问题先标出页码、原文和缺失信息。将提取后的内容整理成[向量问答](../vector_qa/README.md#从教学语料到自己的文档)的文档格式，复用同一组问题，检查增加检索后哪些问题改善、哪些证据反而没有进入上下文。

[主题目录](../README.md) · [课程首页](../../README.md)
