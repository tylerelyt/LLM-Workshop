<a id="lesson-4-reflection-system"></a>

# 反思与改进

以一份故意遗漏规则细节和配件清单的桌游草稿为起点，让评估者指出问题，反思者结构化整理遗漏，生成者改写；学员逐条核对改写是否有依据。模型的自评和文字长度都不能单独证明质量提高。

## 工程任务

模型说自己已经改进了草稿，但新稿可能只是更长。

在 [reflection_system_demo.py](reflection_system_demo.py) 中，固定草稿、模型与任务，只改变是否注入一条已保存的相关反思。

逐个把原始遗漏对应到实际改稿，决定哪些经验值得保存，哪些仍是未经证实的建议。

## 环境与可复现起点

从仓库根目录安装依赖，按[模型配置](../../README-DEEPSEEK.md)导出课程 `OPENAI_*` 变量。语义召回使用下列本地嵌入模型，首次使用需要准备模型权重；也可按源码使用 DashScope 嵌入。

```bash
python -m pip install -r chapter9/reflection/requirements.txt
export WORKSHOP_LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
REFLECTION_RUN="$(mktemp -d)"
cat > "$REFLECTION_RUN/draft.txt" <<'DRAFT'
设计一款八人桌游：玩家暗选忠臣或反贼，通过日间投票与夜间行动争夺胜利。
DRAFT
python chapter9/reflection/reflection_system_demo.py --memory-file "$REFLECTION_RUN/memory.json" --baseline-file "$REFLECTION_RUN/draft.txt" --output "$REFLECTION_RUN/first.json"
```

先手工列出草稿至少两处缺失，例如平局处理、配件数量或人数适配，再运行。固定草稿使缺口可见；接口和嵌入不可用属于环境问题，不能把它们作为“反思失败”的教学证据。

## 看实际产物

终端默认展示原稿、模型评估、遗漏建议与实际改稿差异，不再用字数增长代替效果对照。评估正文显示前 500 字、差异显示前 36 行并提示截断；用命令中的 `--output` 文件逐项核对完整正文。


依次打开报告中的 `original_content`、`evaluation`、`reflection.omissions` 与 `improved_content`。为每个遗漏写出“原稿是否确实缺少 → 改写对应段落 → 是否满足原始任务”的人工判定。运行代码保持不变，允许修改的变量是下一轮的草稿内容。

打开 `memory.json`，核对持久化条目的主题、描述、建议与本轮反思一致。程序提供参考流程，不要求学员修改判定器或把模型自评改成 PASS。

## 在新进程中检查召回

保留同一草稿、任务与模型，仅让第二个进程使用已写入的记忆：

```bash
python chapter9/reflection/reflection_system_demo.py --memory-file "$REFLECTION_RUN/memory.json" --baseline-file "$REFLECTION_RUN/draft.txt" --output "$REFLECTION_RUN/second.json"
```

对照 `retrieved_memories` 的真实条目与 `memory_context_in_revision`，检查它们是否进入改写请求，再读新正文是否采用相关建议。记忆文件非空但取不到嵌入时，程序会报告召回不可用，不把文件存在当作已完成记忆检索。

两次仍有模型采样波动。报告可证明保存、召回与输入组装；要证明稳定质量提升，还需要固定任务与独立人工标准的多次对照。

## 独立验收与重跑

提交原稿、两份报告、记忆条目及至少两项逐段核对。将草稿补齐一处已知遗漏，使用新的空白记忆路径再运行，只改草稿这一项；检查评估者是否还把已补齐的内容误报为遗漏。

每组实验使用新的输出目录。只删除本次 `REFLECTION_RUN`，不改脚本同目录下的既有记忆文件。归档和核心字段选择的另一种实现见[持久记忆](../../chapter8/persistent_memory/README.md)。

终端默认展示原稿、模型评估、遗漏建议与实际改稿差异，不再用字数增长代替效果对照。评估正文显示前 500 字、差异显示前 36 行并提示截断；用命令中的 `--output` 文件逐项核对完整正文。

## 在自己的项目中使用

选一个有明确质量标准的实际产物，先由人标注缺陷，再比较修改前后是否逐项解决。将经过复核的经验放入[持久记忆](../../chapter8/persistent_memory/README.md)，用新的同类任务验证是否有迁移价值。

[主题目录](../README.md) · [课程首页](../../README.md)
