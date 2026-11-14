# 法律文书分析

## 工程任务

教学合同存在冲突期限，另有问题询问文中未给出的联系方式。

在 [document_qa.py](document_qa.py) 中，固定问题与模型，只修改副本中一条合同条款。

对照条款原文解释冲突与未知信息，修订一处条款后核对答案是否跟随新证据。

## 学习目标

在不建立检索索引的条件下，把一份文书作为上下文，利用条款编号识别内部冲突和信息缺口，并用一次受控修订解释答案变化。

## 前置条件与起点

使用 Python 3.11 或 3.12。按模型配置说明准备服务。使用兼容 OpenAI 的聊天服务时，在另一个终端启动模型桥接。本课独立于图片/OCR 对照与按页提取。[模型配置](../../README-DEEPSEEK.md#setup)

```bash
python -m pip install -r chapter6/legal_qa/requirements.txt
python chapter6/legal_qa/document_qa.py --show-document
```

程序先显示随课提供的 `data/legal_document.txt`。它是教学构造的软件交付合同节选，`[C3]` 与 `[C4]` 对同一交付期限分别写了 7 天和 10 天。读完后先记录冲突所在，并确认文书没有电话号码。`--show-document` 只展示资料，不调用模型。

## 动手任务

固定默认问题，先运行基线。

```bash
python chapter6/legal_qa/document_qa.py
```

程序打印实际输入的文书、问题和答案。核对它有没有引用 `[C3]` 与 `[C4]` 的原文，并说明电话信息缺失。用下面的参数提出自己的问题，无需改基础代码。

```bash
python chapter6/legal_qa/document_qa.py --question '合同价款何时支付？引用条款编号。'
```

接着只修改一项证据。在自己的临时目录复制样例，把副本中 `[C4]` 的“10 个自然日”改为“7 个自然日”，其余内容保持不变，再用同一个默认问题运行。

```bash
LAB_DIR=$(mktemp -d)
cp chapter6/legal_qa/data/legal_document.txt "$LAB_DIR/revised.txt"
# 编辑 "$LAB_DIR/revised.txt" 中 C4 的交付期限后运行
python chapter6/legal_qa/document_qa.py --document "$LAB_DIR/revised.txt"
```

本轮学员只改文书副本、`--question` 或 `--document`。每次调用使用新消息，不把上一轮模型结论作为原文。保留副本可复跑，重新复制样例即可回到基线。

## 验收要求

对照基线与修订版的实际文书、同一个问题及两份回答。基线应列出冲突的两个条款，修订版应根据两处一致的期限更新判断。两轮都应说明缺少联系电话。检查每个引用和结论能否由当轮原文支持，不能只看回答是否含有“冲突”或“信息不足”等词。

## 在自己的项目中使用

选择自己能够复核的条款材料，先标注现行版本、冲突条件与文中没有提供的信息，再检查逐条回答。需要处理多份材料时，进入[向量问答](../vector_qa/README.md)，把版本适用性和证据不足问题保留在题集中。

[主题目录](../README.md)
