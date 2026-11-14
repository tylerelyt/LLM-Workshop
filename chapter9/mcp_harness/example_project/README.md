# Harness 要处理的示例项目

这是MCP Harness 练习提供给 Agent 的目标代码，包含一个故意保留的小数除法缺陷。Harness 的客户端和 MCP Server 位于[上一级课时目录](../README.md)。

- `calculator.py`：提供 `divide(left, right)`，当前使用 `//`，因此 `7 / 2` 的结果错误。
- `test_calculator.py`：检查整数结果、小数结果与零除异常；起点中的小数测试应失败。
- `AGENTS.md`：Agent 在新会话中读取的项目约定。

按课时说明复制到临时目录，再让 Agent 修复副本、增加边界测试并重跑。保留随课原版，便于每次从相同缺陷开始。
