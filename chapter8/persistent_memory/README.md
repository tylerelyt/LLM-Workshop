<a id="lesson-5-memgpt-风格的持久记忆"></a>

# 持久记忆

本课用本地 JSON 展示 MemGPT 风格的记忆组织：新进程创建智能体时，把最近的核心经验、反思模式和用户信息放进系统消息。它使用 AutoGen 和应用代码，不是 MemGPT 托管服务，也没有自动的归档检索。

## 工程任务

记忆文件已写入，当前智能体却可能继续使用创建时的旧系统消息。

在 [memgpt_integration_demo.py](memgpt_integration_demo.py) 中，固定任务、模型及其余文件，只修改 Actor 的一条 human_info 偏好，再用新进程运行。

在新进程里追踪一条用户偏好到首次回答，判断它只是被读入还是已经被采用。

## 空白起点与第一次运行

从仓库根目录运行，先按[模型配置](../../README-DEEPSEEK.md)导出课程 `OPENAI_*` 变量。

```bash
python -m pip install -r chapter8/persistent_memory/requirements.txt
MEMORY_RUN="$(mktemp -d)"
python chapter8/persistent_memory/memgpt_integration_demo.py --memory-dir "$MEMORY_RUN/store" --output "$MEMORY_RUN/first.json"
```

任务固定为智能家居方案。先预测：新目录里没有历史事实，程序能从哪里获得用户偏好？在首轮报告中检查 `loaded_memory` 应为空，而不是因为生成了一份 JSON 文件就声称模型已经有历史记忆。

## 写入后，用新进程读回

```bash
python chapter8/persistent_memory/memgpt_integration_demo.py --memory-dir "$MEMORY_RUN/store" --output "$MEMORY_RUN/second.json"
```

本次会创建三个新的智能体对象。逐一对照 `actor_reflection_memory.json`、`evaluator_reflection_memory.json`、`reflector_reflection_memory.json` 与报告的 `loaded_memory`，标出哪些条目进入了各角色的系统消息。

| 字段 | 实际行为 |
| --- | --- |
| `core_memories` | 保留最近15条，创建提示时取最近5条 |
| `reflection_patterns` | 创建提示时取最近3条 |
| `human_info` | 作为用户信息写入提示 |
| `archival_memories` | 仅保存，本实现不会自动检索 |

`memory_enhanced` 表示新建智能体时确实加载了内容，不表示回答一定更好。写文件不会修改已经创建的智能体提示；验证新记录要使用新进程或显式重建对象。

## 改一个变量与独立验收

保留任务、模型和其余文件，只在 Actor 的 `human_info` 增加一条与任务有关的偏好，例如“方案必须覆盖断网时的本地控制”，保存备份后用新进程运行到第三份报告。核对该偏好进入 `loaded_memory.Actor`，再检查答案是否真正满足约束。读入与采用分开判定。

将第二次运行改用新的空目录，可作为无持久状态的对照；不要改动模型或任务来解释“记忆使回答更好”。每轮保存到不同报告文件，保留采样变化和未采用约束的失败结果。

提交三份运行报告、一条记忆到系统消息再到答案的证据链，并说明当前 Session 历史与跨进程持久文件的区别。只清理自己创建的 `MEMORY_RUN` 目录。

终端先显示三个新建智能体实际注入的历史记忆，再显示本轮首次回答、评估、反思和改稿差异。持久文件保存实际任务约束与反思内容；查看历史偏好是否出现在首次回答中，避免把本轮改稿误当作跨会话记忆的效果。较长内容显示摘要，完整内容在 `--output` 文件。

## 在自己的项目中使用

为自己的任务区分用户偏好、已完成事项与临时观察，分别决定何时写入、更新和读取。加入一次用户纠正并用新进程验证，检查旧信息是否仍影响回答；需要保存完整证据时，参考[文件系统记忆](../filesystem_memory/README.md)。

[主题目录](../README.md) · [课程首页](../../README.md)
