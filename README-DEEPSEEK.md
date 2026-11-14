<a id="run-the-workshops-with-an-openai-compatible-chat-model"></a>

# 使用兼容 OpenAI 的聊天模型运行课程

课程通过 OpenAI SDK 调用 Chat Completions。早期推理示例、模型驱动的 RAG、多智能体和 MCP Harness 可以共用同一套模型配置。部分练习还需要本地模型、外部工具或独立授权。

<a id="setup"></a>

## 环境准备

在仓库根目录使用 Python 3.11 或 3.12。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-deepseek.lock
cp .env.example .env
```

将下列配置写入已忽略的 `.env` 文件，或在终端导出环境变量。填写提供方的 API 基础地址和准确的模型标识。

```dotenv
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=your-model-id
OPENAI_API_KEY=your-provider-key
```

基础地址包含提供方要求的版本前缀，例如 `/v1`，SDK 会追加 `/chat/completions`。Agent 练习需要模型支持工具调用；使用 JSON 模式的 RAG 练习还需要支持 `response_format: {"type":"json_object"}`。

上述三个 `OPENAI_*` 变量均未设置时，仍可使用已有的 `DEEPSEEK_*` 配置，默认地址为 `https://api.deepseek.com`，模型为 `deepseek-flash`。`DEEPSEEK_ENV_FILE` 可以指定保存这两类配置的本机环境文件。支持 `--model` 的命令可用它覆盖配置中的模型名。

各主题需要在线调用模型的独立脚本需要在当前终端导出三个 `OPENAI_*` 变量。使用 DeepSeek 时，地址填写 `https://api.deepseek.com`，模型填写 `deepseek-flash`。密钥通过环境变量提供，各课额外依赖见对应 `requirements.txt`。

<a id="chapters-1-and-2-run-the-ollama-examples-with-your-chat-model"></a>

## 直接调用课程模型接口

提示、推理、历史管理、文档问答和工具练习直接调用兼容 OpenAI 的 Chat Completions 服务，不需要额外启动协议桥接。先按上面的配置填写 `.env` 或导出 `OPENAI_*`，再安装各练习自己的依赖。

LangChain 练习保留原来的工作流或 Agent 循环，通过 `workshop_runtime.langchain_llm.WorkshopLLM` 使用同一套模型接口。手写工具调用与 AutoGen 使用相同的业务函数和独立检查，比较时保持问题、模型、数列数量与随机种子一致。

`WORKSHOP_LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5` 可为向量问答、NL2SQL、反思记忆和分类练习选择较小的本地嵌入模型。需要下载模型权重的练习见各自说明。分类练习的 `--feature-cache` 可保存冻结特征，随后固定特征与划分比较分类头参数，不重复调用嵌入模型。

<a id="rag-retrieval-maintenance-and-harness-integration"></a>

## RAG 独立练习与批量检查

各项独立练习见[提示工程方法](chapter6/README.md)。批量检查与共享语料见 RAG 运行器说明。[RAG 练习](chapter6/shared/rag/README.md)

```bash
python -m chapter6.shared.rag all --output chapter6/shared/rag/results/offline.json
python -m chapter6.shared.rag all --live --output chapter6/shared/rag/results/live.json
python -m chapter6.shared.rag reranker --live
python -m chapter6.shared.rag mcp --live
```

首个练习是一个独立文件，内置样例文档，并用连续的 `# %%` 单元展示索引、召回、重排、提示组装和答案生成。

```bash
python chapter6/reranking/reranker/lab.py
```

在终端设置 `DASHSCOPE_API_KEY`。该文件只使用 Python 标准库，默认通过 DashScope 调用 `text-embedding-v4`、`qwen3-rerank` 和 `deepseek-v4.1-flash`，并在内存中建立索引。直接运行此文件时，准备 DashScope 配置即可，样例与数据均已内置。[重排实验说明](chapter6/reranking/reranker/README.md)

将答案生成切换到其他 Chat Completions 提供方时，导出上面的三个 `OPENAI_*` 变量。嵌入与重排调用仍使用 DashScope 密钥。

RAG 运行器在在线模式执行同一个文件。省略 `--live` 时读取历史快照。其他阶段使用各自的教学样例，MCP 阶段使用共享语料和本地 BGE 索引。

<a id="chapter-6-lesson-2-framework-tools-mcp-and-cli-skills"></a>

## 独立工具接入练习

各项练习分别配置、运行和验收：

- [框架工具调用](chapter8/autogen_tool_loop/README.md)：AutoGen 接管手写调用任务。
- [MCP 基础](chapter9/mcp_tools/README.md)：发现工具、发送调用并读取结果。
- [飞书远程 MCP](chapter9/feishu_mcp/README.md)：准备用户凭证并连接远程服务。
- [CLI Skill](chapter9/cli_skills/README.md)：扫码授权、搜索文档、复用授权并封装脚本。
- [Pi SDK](chapter9/pi_skills/README.md)：对照加载技能前后的文档读取。

MCP 计算器可先列工具，再使用已配置的聊天模型决定调用：

```bash
python chapter9/mcp_tools/mcp_harness.py list-tools
python chapter9/mcp_tools/mcp_harness.py run \
  --task '调用 calculator 计算 sqrt(2) * 100，保留两位小数。'
```

飞书凭据与模型 API 密钥分别配置；CLI 搜索脚本独立运行时不需要模型密钥。

<a id="references"></a>

## 参考资料

- [DeepSeek 模型与 API](https://api-docs.deepseek.com/quick_start/pricing/)
- [思考模式与工具消息](https://api-docs.deepseek.com/guides/thinking_mode/)
- [FastEmbed 支持的模型](https://qdrant.github.io/fastembed/examples/Supported_Models/)
