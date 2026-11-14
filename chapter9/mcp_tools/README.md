# MCP 工具发现与调用

让同一个客户端通过标准输入输出通道发现独立进程发布的工具，完成计算和单位换算。验收时要沿着工具参数、实际返回值和最终答案解释一次完整调用。[客户端](mcp_harness.py) · [工具服务](tools_server.py)

## 工程任务

工具移到独立进程后，参数、错误和返回值需要跨过协议边界。

在 [mcp_harness.py](mcp_harness.py) 中，固定题目与模型，只改变 Harness 的循环预算。

根据实际工具发现与调用判断是否接通，再解释本任务是否需要独立服务。

## 先让协议路径可见

使用 Python 3.11 或 3.12，在仓库根目录激活课程环境并安装依赖。理解函数调用与框架调用的区别后即可开始，本练习不依赖其他课生成的文件。[框架工具调用](../../chapter8/autogen_tool_loop/README.md)

```bash
python -m pip install -r chapter9/mcp_tools/requirements.txt
python chapter9/mcp_tools/mcp_harness.py list-tools
```

这一步启动真实的本地 MCP 服务并发现 `calculator`、`unit_converter`、`get_datetime`，无需模型密钥。工具已由讲师实现，学员先看名称、描述和参数结构，画出客户端与工具进程之间的边界。依赖或启动失败时先修复环境，直到列表可见，再进入模型调用。

## 预测、运行，再换一个任务

在当前终端配置支持工具调用的聊天模型，导出 `OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_API_KEY`。也可使用课程已有的 `DEEPSEEK_*` 配置。[模型配置](../../README-DEEPSEEK.md)

先预测 `sqrt(2) * 100` 保留两位小数的值，再运行。为每次实验指定不同的结果目录。

```bash
python chapter9/mcp_tools/mcp_harness.py run \
  --task '调用 calculator 计算 sqrt(2) * 100，保留两位小数。' \
  --output-dir chapter9/mcp_tools/results/calculator-01
```

结果应能与 `141.42` 对上。在 `mcp_harness_report.json` 中找到 `tool_calls`，检查实际函数名、表达式、返回文本与 `answer`。即使模型直接写对答案，也要检查是否真的调用了工具。

保持模型、工具服务和运行参数不变，只把任务换成单位换算。先在列表中确认单位名称，预测 100 摄氏度对应多少华氏度，再运行。

```bash
python chapter9/mcp_tools/mcp_harness.py run \
  --task '调用 unit_converter 将 100 celsius 换算为 fahrenheit。' \
  --output-dir chapter9/mcp_tools/results/temperature-01
```

确认实际调用的是 `unit_converter`，输入值为 100，源单位和目标单位分别为 `celsius`、`fahrenheit`，实际结果支持 `212.0 fahrenheit`。解释为什么这次模型应选择另一项工具。学员改变任务和输出目录，保留提供的工具实现与调用循环，避免直接把期望答案写进工具。

## 验收与重跑

保留两份报告，分别指出工具参数、真实返回值、模型获得的观察和最后结论。报告的 `success` 表示调用循环是否结束，数值是否正确、单位是否匹配、模型是否实际用工具仍需按上述证据核对。

`list-tools` 只验证本地协议发现，`run` 还涉及所配置的在线模型。重跑时换一个结果目录，避免覆盖对照记录。清理时只删除本课自己指定的结果目录。

[飞书远程 MCP](../feishu_mcp/README.md#remote-mcp) · [主题目录](../README.md)

## 在自己的项目中使用

选择一个已能独立运行的纯函数，将它暴露为只读工具，检查结构发现、参数错误和实际结果。需要访问知识库时继续做[检索服务接入](../rag_mcp/README.md)；需要企业身份时，另行学习[飞书 MCP](../feishu_mcp/README.md)的授权与权限。
