<a id="lesson-1-multimodal-image-analysis"></a>

# 多模态图像分析

对照把原图发送给视觉模型与先提取图片文字两种方式。查看样例图片，检查每条路径保留了哪些证据。

## 工程任务

图片中的版式、位置和文字都可能影响答案，只做 OCR 可能丢失重要信息。

在 [image_analyzer.py](image_analyzer.py) 中，先固定同一个具备视觉与文字能力的模型及问题，只改变 --ocr 输入路径。

对照同一问题的两条输入路径，决定当前任务是否需要视觉信息，并说明依据。

## 学习目标

- 识别图片中的文字，并对照原图核对抄录内容。
- 利用视觉版式和内容回答问题。
- 总结有依据的事实，同时标出无法辨认的文字。
- 对照直接理解图片与先做 OCR、再分析文字两种方式。
- 处理 PNG、JPEG 和 WebP 格式的图片。

<a id="environment-setup"></a>

## 环境准备

使用 Python 3.11 或 3.12，在仓库根目录安装本课依赖。

```bash
python -m pip install -r chapter6/image_context/requirements.txt
```

通过 `OPENAI_BASE_URL`、`OPENAI_MODEL` 和 `OPENAI_API_KEY` 配置支持图片输入的 Chat Completions 模型。原有的 Qwen-VL 路径使用 `DASHSCOPE_API_KEY`。两轮对照使用同一套模型配置。[课程模型配置](../../README-DEEPSEEK.md) · [DeepSeek 图片输入](https://api-docs.deepseek.com/guides/vision/)

使用提供的 `sample_image.jpg`，或一张可以直接检查内容的图片。`--ocr` 对照路径依赖 macOS Vision 和 Swift。先运行下面的命令只查看提取文本，此时不调用模型。

```bash
python -m chapter6.image_context.image_analyzer --ocr-only
```

起点是同一张可人工检查的图片及其 OCR 文本。先预测仅凭文字能否判断文字方向，再进行两轮模型对照。

<a id="compare-two-inputs"></a>

## 对照两种输入

先看样例图片，记下最右一列写了什么、每列从哪边开始读。从仓库根目录向两条路径提同一个问题。

```bash
QUESTION='请说明文字方向，抄录最右侧的一列黑字，再抄录它左边第一列的开头八个字。只用可见证据，不确定的字标为〔不清〕。'
python -m chapter6.image_context.image_analyzer --prompt "$QUESTION"
python -m chapter6.image_context.image_analyzer --ocr --prompt "$QUESTION"
```

第一条把原图发给模型。第二条先显示 macOS Vision 提取的文字，再把文字发给同一个模型。对照原图核对「老子」「道可道非常道名可」及竖排方向，记录哪条路径保留了作答需要的证据。

分析其他图片时，把图片路径作为位置参数传入。省略 `--prompt` 时，两条路径都使用本课默认的文字方向与抄录问题。

```bash
python -m chapter6.image_context.image_analyzer chapter6/image_context/sample_image.jpg \
  --prompt 'Identify the main subject and quote the visible text that supports your answer.'
```

分析器把图片放入标准的 `image_url` 内容块，检测图片格式、编码文件，然后返回模型的分析结果。OCR 模式把提取的文字和问题发送给配置好的聊天模型。

<a id="file-structure"></a>

## 文件结构

```text
image_context/
├── image_analyzer.py       # Vision API and OCR comparison entry point
├── recognize_text.swift    # Local OCR on macOS
├── requirements.txt        # Python dependencies
├── sample_image.jpg        # Image for the comparison
└── README.md
```

<a id="practice-and-acceptance"></a>

## 练习与验收

1. 用提供的图片运行两条路径，保留问题、OCR 提取文本和两份答案。
2. 标出与图片一致的抄录文字和版式判断，记录无法辨认的字。
3. 先固定图片、模型和问题，只切换原图与 OCR 输入。再固定图片与模型，只修改 `--prompt`，比较识别与分析结果。若换图，另开一组记录。
4. 要求模型给出简短摘要，检查其中每个主要判断能否追溯到可见文字或版式。

以原图作为验收依据，逐条标记正确、错误或证据不足。OCR 未提取出的版式信息应被识别为证据缺口。答案较长或语气更确定不能代替核对。学员本轮只改变命令行的问题或图片，不需要修改 OCR 基础设施。两次调用各自新建请求，可重用同一张图片与问题复跑。

本练习可以继续扩展到文档版式分析、多模态知识图谱和跨模态融合。原图与提取文本为评价这些后续步骤提供证据。

<a id="common-issues"></a>

## 常见问题

| 现象 | 排查内容 |
|---|---|
| API 配置错误 | 核对当前环境中的服务地址、模型 ID 和密钥，并使用支持图片输入的模型。 |
| 图片格式不支持或无法读取 | 检查文件是否为有效的 PNG、JPEG 或 WebP 图片，并确认能在本机打开。 |
| OCR 无法运行 | 在装有 Swift 的 macOS 中使用 `--ocr`，先核对打印出的提取文本，再评价模型答案。 |
| 缺少依赖 | 使用课程 Python 环境，并安装本课 `requirements.txt` 中的依赖。 |

## 在自己的项目中使用

从自己的资料选择一张答案依赖布局、箭头或图例的图片，人工标出证据位置，再比较原图与 OCR 输入。将这类缺口带入[文档提取](../document_qa/README.md)流程，决定哪些页面需要保留图像，哪些可以只使用文本。

[主题目录](../README.md) · [课程首页](../../README.md)
