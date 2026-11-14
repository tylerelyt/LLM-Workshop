# 代码转换与行为校验

## 工程任务

生成的 JavaScript 看起来像 Python 原程序，却可能在初值、更新顺序或边界处改变行为。

在 [code_translation.py](code_translation.py) 中，固定源程序、测试输入和 Harness，只更换具备代码生成能力的模型。

用真实运行的空输入、单元素和相邻长度结果判断转换，而不是只看代码能否解析。

## 学习目标

把 Python 的 Fibonacci 生成器改写成 JavaScript，用实际运行结果检查初始值、更新顺序和终止条件是否保留。

## 前置条件与起点

使用 Python 3.11 或 3.12 和可运行 `node --version` 的 Node.js。按模型配置说明准备服务，使用兼容 OpenAI 的聊天服务时，在另一个终端启动模型桥接。[模型配置](../../README-DEEPSEEK.md#setup)

```bash
python -m pip install -r chapter8/code_translation/requirements.txt
```

本课给定 Python 生成器，前五项应为 `0、1、1、2、3`。程序打印实际源代码与 Python 输出，模型负责生成同名的 `function* fibonacci(n)`。学员先预测 `n=0`、`n=1`、`n=5` 的结果，再观察转换。

## 动手转换与语义核对

为本次练习准备输出目录，生成 JavaScript 后先打开文件，检查它是否只包含本课生成器和打印示例。

```bash
LAB_DIR=$(mktemp -d)
python chapter8/code_translation/code_translation.py --count 5 --output "$LAB_DIR/fibonacci.js"
python chapter8/code_translation/code_translation.py --check "$LAB_DIR/fibonacci.js" --count 5
```

`--check` 执行检查过的文件，在新的 JavaScript 上下文里调用其中的 `fibonacci`，对照 Python 结果。它显示 `n=0`、`n=1`、本次次数和次数加一时的两种输出。结果不一致、循环不结束或函数不能调用时退出失败。此步骤不调用模型。

## 只改一个变量

先保留同一份 JavaScript，只把检查命令的 `--count` 改为 `8`，看它能否处理新的输入。再复制文件，把更新语句中用到旧值的顺序故意改错，重跑同一组检查。解释第一处错误的输出怎样对应到更新顺序。恢复副本后重跑，保留前后轨迹。

可编辑范围是转换后的生成器及 `--count`。检查器里的 Python 参考实现作为本课基础设施保留。使用新文件名保留失败版本，重新运行生成命令可以新建模型转换结果。

## 验收要求

提交 Python 程序、JavaScript 程序，以及正常版本和故意改错版本的执行对照。至少核对空序列、首项、前五项和更长输入，说明问题出在初始值、更新顺序还是终止条件。文件生成和代码语法正确分别作为中间结果，最终依据是两种语言在相同输入下的实际序列。

## 在自己的项目中使用

选择一个自己维护的小函数，先写正常、空输入与边界行为的独立测试，再进行语言转换。把执行失败与行为偏差交回模型修订，并参考[代码解释器](../code_interpreter/README.md)研究怎样用实际运行反馈驱动修改。

[主题目录](../README.md)
