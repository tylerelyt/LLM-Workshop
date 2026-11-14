# 自一致性

同一道题多问几次，再投票，会更可靠吗？本练习把解析成功、形成多数和答案正确分开，观察增加调用次数的收益与代价。

## 先看两种失败

从仓库根目录安装依赖。下面三组都是明确标注的教学回复回放，不会调用模型。

```bash
python -m pip install -r chapter7/self_consistency/requirements.txt
python chapter7/self_consistency/example1.py --replay chapter7/self_consistency/data/valid_majority.json
python chapter7/self_consistency/example1.py --replay chapter7/self_consistency/data/wrong_majority.json
python chapter7/self_consistency/example1.py --replay chapter7/self_consistency/data/abstain.json
```

运行前，逐条计算有效答案数和票数，预测是否会接受多数。第二组能形成多数，但多数答案错误；第三组没有超过总尝试次数一半的同一答案，程序应弃权。无效格式仍计入总尝试次数，不能为了得到多数而悄悄丢掉失败样本。

退出码 `0` 表示多数答案符合独立答案，`1` 表示多数答案错误，`2` 表示弃权或参数无效。结合输出和 JSON 中的 `abstained` 区分这些情况。回放检查证明投票机制的行为，不能用来比较在线模型能力。

## 再比较真实采样

按[模型配置](../../README-DEEPSEEK.md#setup)设置课程 `OPENAI_*` 变量。请求直接发送到兼容 Chat Completions 的服务。

```bash
python chapter7/self_consistency/example1.py --trials 1 --output /tmp/vote-single.json
python chapter7/self_consistency/example1.py --trials 3 --output /tmp/vote-three.json
```

保持题目、模型与解析规则一致，记录完整回复、有效数、票数、正确性、调用数、用量和总耗时。在线模式的总耗时覆盖这一组生成请求；本轮接口未报告的用量不自行估算。

默认题目是 `10 + 20 + 30`，独立答案为 `60`。自拟一道更容易出现分歧的题时，先独立计算答案，再同时传入 `--question` 和 `--expected`；不要事后把期望值改成模型的多数答案。只解析单独一行的“最终答案：数值”，支持零、负数与小数。

## 做出判断

比较单次正确率、形成多数的比例与多数正确率，并保留弃权结果。一次三票一致不说明策略稳定有效；在自己选定的同一组题目上重复观察，再说明增加请求是否值得，以及哪些任务需要工具或外部证据。

## 在自己的项目中使用

先为一组实际任务准备独立参考答案，再比较单次与多次求解的正确、错误和弃权分布。若错误来自缺少资料或计算失误，分别对照[检索问答](../../chapter6/vector_qa/README.md)与[计算工具](../../chapter8/calculator_agent/README.md)，判断额外采样是否是合适的投入。

[推理练习](../README.md) · [课程首页](../../README.md)
