<a id="lesson-3-filesystem-as-context-and-externalized-memory"></a>

# 文件系统上下文与外部记忆

本课学习 Manus 利用文件系统承载 Agent 上下文的做法，将大段资料保存在文件中，再按任务读取需要的内容；每次发送给模型的输入仍受上下文窗口限制。

## 工程任务

长观察放不进上下文，进程重启后又需要继续工作。

在 [filesystem_memory_demo.py](filesystem_memory_demo.py) 中，固定已保存数据，只改变恢复时选取的上下文字段。

说明哪些内容必须持久保存、哪些可以摘要，以及恢复时怎样回查完整证据。

## 🎯 学习目标

- **文件系统上下文**，理解用文件系统承载 Agent 记忆的设计思路
- **可恢复压缩**，实现能够还原原始内容的上下文压缩策略
- **状态外置**，将长期状态从上下文转移到文件系统
- **SSM 架构**，探索状态空间模型在 Agent 中的应用前景

<a id="-limitations-of-traditional-approaches"></a>

## 🚫 传统方法的限制

<a id="context-window-dilemma"></a>

### 上下文窗口的困境

即使模型支持 128K 以上的 token 窗口，实际应用仍面临挑战。

1. **观察结果膨胀**，网页、PDF 等非结构化数据容易超出窗口限制
2. **性能下降**，超长上下文可能影响模型表现
3. **成本增加**，即使有前缀缓存，长输入仍然带来较高成本

<a id="risks-of-compression-strategies"></a>

### 压缩策略的风险

- **信息丢失**，过度压缩可能删去关键内容
- **难以预判**，无法提前确定哪条观察结果会在十步之后变得重要
- **不可逆性**，无法恢复原文的压缩方式会带来风险

<a id="-manuss-filesystem-solution"></a>

## 💡 Manus 的文件系统方案

<a id="core-philosophy"></a>

### 核心理念

> 用文件系统承载外部上下文，获得超出窗口限制的容量、自然持久化和直接操作能力。

<a id="key-features"></a>

### 主要能力

- **容量扩展**，存储不受 token 窗口限制
- **持久保存**，跨会话保留状态
- **直接操作**，Agent 可以通过读写文件管理记忆
- **可恢复压缩**，压缩内容时保留恢复完整信息的路径

<a id="-practice-and-extensions"></a>

## 🛠️ 实践与扩展

<a id="exercise-1-filesystem-memory-manager"></a>

### 练习一：文件系统记忆管理器

构建管理器，将 Agent 的状态和记忆存入文件系统。

<a id="exercise-2-recoverable-compression-engine"></a>

### 练习二：可恢复压缩引擎

为网页、文档等大型观察结果实现可恢复的压缩机制。

<a id="extension-ssm-agent-prototype"></a>

### 扩展：SSM-Agent 原型

设计状态空间模型如何使用同一套文件系统记忆接口。

<a id="-file-descriptions"></a>

## 📁 文件说明

`filesystem_memory_demo.py` 在一个文件中实现观察结果存储、可恢复压缩和状态持久化。

<a id="-practical-cases"></a>

## 🚀 应用案例

<a id="case-1-long-term-project-management"></a>

### 案例一：长期项目管理

Agent 处理持续数周的复杂项目，通过持久化存储维护状态。

<a id="case-2-large-document-processing"></a>

### 案例二：大型文档处理

处理数百页 PDF 时，先压缩内容，再按需恢复原文。

<a id="case-3-web-browsing-history"></a>

### 案例三：网页浏览历史

浏览大量网页时，组织和检索相关信息。

<a id="-architecture-design"></a>

## 🏗️ 架构设计

```python
# Core concept of filesystem as context
class FilesystemContext:
    def compress_observation(self, obs, preserve_key):
        """Recoverable compression: preserve key info, remove details"""

    def restore_observation(self, key):
        """Restore complete observation from filesystem"""

    def externalize_state(self, state):
        """Write agent state to files"""

    def internalize_state(self):
        """Restore agent state from files"""
```

<a id="-design-principles"></a>

## 💡 设计原则

> “文件系统为 Agent 提供持久、可恢复的外部记忆。模型按需读写文件，利用其中有组织的信息继续任务。”
> — Manus AI 团队

<a id="key-implementation-strategies"></a>

### 实现策略

- **保留 URL**，网页正文可以暂时移出上下文，但要保留访问地址
- **维护路径**，文档内容可以压缩，文件路径应在沙箱中可用
- **结构化存储**，用目录结构组织外置状态
- **延迟加载**，只在需要时恢复详细内容

<a id="-forward-thinking-ssm-agent"></a>

## 🔮 前瞻：SSM-Agent

<a id="potential-of-state-space-models"></a>

### 状态空间模型的潜力

传统 Transformer 依赖全注意力机制，SSM 则提供了另一种探索方向。

- **速度优势**，SSM 推理具有加速潜力
- **效率特点**，无需维护完整上下文的注意力计算
- **文件系统集成**，将长期依赖外置，模型聚焦短期决策

<a id="envisioned-agent-architecture"></a>

### 架构设想

```
SSM Core + Filesystem Memory = Next-Generation Agent
├── Fast Inference: SSM handles immediate decisions
├── Long-term Memory: Filesystem stores historical state
└── Smart Retrieval: Load relevant context on demand
```

<a id="-getting-started"></a>

## 🚀 开始运行

从仓库根目录运行本地演示。

```bash
python chapter8/filesystem_memory/filesystem_memory_demo.py --demo all
```

用 `--demo observations`、`--demo states` 或 `--demo persistence` 单独运行一个阶段。记录压缩后保留了哪些字段，再检查能否恢复完整的观察结果和已保存状态。

### 用两个进程证明持久化

教学场景先完成资料搜索，再把分析阶段交给下一次运行。先创建新的工作目录，并预测新进程能读取到哪些信息。以下两条 Python 命令分别创建新的管理器对象，只有工作目录相同。

```bash
memory_dir="$(mktemp -d)"
python chapter8/filesystem_memory/filesystem_memory_demo.py --demo persistence \
  --phase save --workspace "$memory_dir"
python chapter8/filesystem_memory/filesystem_memory_demo.py --demo persistence \
  --phase resume --workspace "$memory_dir"
```

第一轮保存包含 100 条结果的完整观察、压缩引用和 `completed_search` 状态。第二轮应恢复同一份完整观察，打印原来的 `next_steps`，再写入 `analyzing_results` 状态。检查 `memory_index.json` 的 `states` 是否保留两个不同 ID，以及各状态文件里的 `agent_state` 是否分别对应搜索完成和分析进行中。更换为空目录后直接执行 `--phase resume`，应提示先保存，避免把空索引误当成恢复成功。

### 只改变保留字段

在 `demonstrate_cross_session_persistence` 调用 `externalize_large_observation` 的位置，仅向 `preserve_keys` 增加 `results`。使用新的 `memory_dir` 重跑相同两轮，比较压缩引用长度和需要恢复才能取得的字段。保留全部结果会增加当前上下文中的引用体积，完整原文仍保存在 `observations` 目录。

提交两轮命令、恢复出的具体状态与下一步、两个版本的状态内容，以及改变保留字段前后的引用长度。引用中的 `compressed_size` 应等于该引用的 UTF-8 字节数。这里测量本地 JSON 的外置与恢复，存储容量还受磁盘限制，模型是否会正确选取这些记忆需要接入 Agent 后继续验证。

保存的 `memory_dir` 会保留供检查。每次独立对照使用新目录，清理时只删除自己创建的该目录。

<a id="-success-metrics"></a>

## 🎯 验收指标

- **记忆持久性**，跨会话的状态保留率
- **压缩效率**，上下文体积的缩减比例
- **恢复准确性**，恢复信息的完整程度
- **操作便利性**，Agent 使用文件操作的便捷程度

---

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

为自己的长任务选择一段原始观察存到文件，只将摘要与路径送入当前输入。重启后通过路径找回原文，核对摘要有没有丢失关键条件；再在[MCP Harness](../../chapter9/mcp_harness/README.md)中观察状态版本与循环接续。

[主题目录](../README.md) · [课程首页](../../README.md)
