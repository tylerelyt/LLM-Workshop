<a id="lesson-1-kv-cache-optimization--prompt-engineering"></a>

# 面向缓存的提示设计

运行本地提示词构建器，观察输出中哪些部分可以形成稳定前缀，再据此分析前缀缓存、只追加上下文和会话路由。

本地 `MemGPTProvider` 和 `RAGProvider` 使用内置教学资料与规则生成记忆分区。先观察请求文本的构造，再通过模型返回的用量判断在线缓存效果。

> **通过提示词与上下文设计，提高 Agent 的缓存复用效率。**

## 工程任务

希望减少重复输入的推理成本，但本地拼接提示更快，并不能说明模型服务更省。

在 [example.py](example.py) 中，固定模型和任务，只改变动态字段在提示中的位置。

区分前缀结构、本地构建耗时和服务实际报告的缓存用量，再判断优化是否成立。

## 🎯 学习目标

* 理解 KV-Cache 怎样影响性能与成本
* 掌握提示词稳定性和上下文设计的工程原则
* 识别并修复导致缓存失效的设计问题
* 说明缓存边界与会话路由在什么条件下能够改善复用

---

<a id="-quick-start"></a>

## 🚀 快速开始

从仓库根目录运行这个单文件提示词构建器。程序使用 Python 标准库。

```bash
python chapter9/prefix_cache/example.py
```

在输出的提示词中找到角色设定、工具、情节记忆和语义记忆四个部分。修改 `run_comprehensive_demo` 中最后一条用户问题，与基线输出对照。记录哪些部分可以一直放在请求开头，哪些内容会随每轮对话变化。性能报告计时的是本地提示词构建过程。缓存命中与首 token 延迟需要通过推理后端测量。

### 固定问题之外，只改变当前查询

这个起点已经包含角色、工具和规则生成的教学记忆。先预测只改查询时哪部分提示应该保持一致，再调用与演示相同的构建入口检查。

```bash
python - <<'PY'
from chapter9.prefix_cache.example import create_demo_scenario

builder = create_demo_scenario()
first = builder.construct_optimized_prompt("请解释 RAG", [])
second = builder.construct_optimized_prompt("请解释 MemGPT", [])
boundary = "└─ END TOOLS ─┘"
first_static = first.split(boundary, 1)[0] + boundary
second_static = second.split(boundary, 1)[0] + boundary
assert boundary in first and boundary in second
assert first_static == second_static
assert first != second
print("相同的角色与工具前缀字符数：", len(first_static))
print("两份提示的动态部分不同：", first != second)
PY
```

允许修改 `example.py` 中 `AdvancedContextPromptBuilder` 的分区排序与 `_format_section_content`。保留人设和工具在前的顺序，将每轮时间戳放在动态分区。试着把时间戳移回人设分区，隔一秒再次构建同一个问题，检查上述前缀相等条件在哪个位置失效，再恢复稳定版本。

交付两份提示中相同的静态前缀和首个变化位置。权重控制动态记忆的顺序，稳定的人设、工具定义与权重相同是这个对照的前提。字符相同证明了请求前缀稳定，在线缓存计数由下一节验证。

<a id="measure-cache-usage"></a>

## 测量缓存用量

安装课程运行环境，配置会返回提示词缓存用量的模型。使用 DeepSeek 时，将 `OPENAI_BASE_URL=https://api.deepseek.com`、`OPENAI_MODEL=deepseek-flash` 和 API 密钥设置在环境变量中。[模型配置](../../README-DEEPSEEK.md)

```bash
python chapter9/prefix_cache/example.py --live
```

记录首次请求、完全相同的重复请求，以及更换首个用户 token 后第三次请求的命中和未命中数量。脚本为每次实验生成新的运行标识，区分各次运行。说明每个请求可以复用哪段前缀。后端按尽力而为的方式构建缓存，脚本报告的是本轮实际观察值。[DeepSeek 上下文缓存](https://api-docs.deepseek.com/guides/kv_cache/)

<a id="-cache-design-patterns"></a>

## 🧪 缓存设计模式

<a id="stable-prefixes"></a>

### 稳定前缀

将可复用内容放在提示词开头。当前时间等每轮变化的值放到后面的部分。

<a id="append-only-context"></a>

### 只追加上下文

将观察结果追加到对话历史中。修改较早的历史条目，可能缩短连续请求之间共享的前缀。

<a id="cache-boundaries-and-session-routing"></a>

### 缓存边界与会话路由

查阅推理后端支持哪些缓存控制方式。如果缓存只存在于各个工作进程内部，将同一会话持续路由到同一个进程，可以增加缓存复用的机会。

<a id="-key-insights"></a>

## 💡 关键认识

> “只要有一个 token 不同，从这个位置开始的缓存就会失效。”

系统提示词、历史上下文和会话标识等设计细节都会影响缓存命中。设计提示词时，应关注怎样尽量复用已有的 KV-Cache。

<a id="-applying-the-patterns-to-an-inference-backend"></a>

### 🎯 将设计模式应用到推理后端

1. **启用前缀缓存**，例如使用 `enable_prefix_caching=True` 参数
2. **管理会话**，通过 `session_id` 保持请求路由一致
3. **组织请求**，将静态文本放在动态文本之前，并在后端支持时使用显式缓存控制
4. **监控性能**，跟踪缓存命中率和响应时间

---

<a id="-further-reading"></a>

## 📚 延伸阅读

* [vLLM 项目](https://github.com/vllm-project/vllm)
* [TGI 项目](https://github.com/huggingface/text-generation-inference)
* [OpenAI 提示词指南](https://platform.openai.com/docs)

---

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

选一组共享系统指令、问题不同的真实请求，先观察稳定前缀，再用服务实际返回的缓存用量核对效果。保持答案质量、输入内容和采样条件可比，并结合[会话历史](../../chapter8/conversation_memory/README.md)区分缓存复用与状态保存。

[主题目录](../README.md) · [课程首页](../../README.md)
