# 项目约定

这是动手工作坊中的 Python 计算模块，只使用标准库。

- 保留 `divide(left, right)` 的接口和零除异常。
- 先读相关源码与测试，做小范围修改。
- 运行 `python3 -m unittest -v`，依据真实输出修复问题。
- 可以补充边界测试，不通过修改已有断言掩盖错误。
- 用户要求列计划时，通过 `update_context` 更新计划 Resource；完成后更新进度。
