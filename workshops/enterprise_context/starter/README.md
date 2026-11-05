# 项目知识平台：起始系统

这是课程隔离环境。全局检索已经可以运行，当前任务是 Jira `KNOW-201`：为 Atlas 项目增加项目检索和文档变更订阅。企业上下文通过旁边的 MCP 服务取得，页面 `100` 是现状与需求，`101` 是已采用的历史决定，`102` 是当前 SDK 接口。

运行已有功能：

```sh
python3 src/application.py --query 检索
```

`shared/wiki_sdk.py` 是多个应用共用的既有 SDK，本轮保持文件内容不变。课程 SDK 读取 `data/wiki.json`；企业 REST 请求发生在独立的 `integration/` 适配层，不能把本地文件读取称为企业 API 调用。

新增功能应保留 `KnowledgeApplication(sdk).search(query)` 的旧行为。为了便于现场核验，新增接口采用：

```python
app.search(query, project_key="atlas")
state = app.subscribe("atlas")
result = app.poll(state)  # {"notifications": [...], "state": 可序列化的后续状态}
```

通知至少能定位 `page_id`、`version` 与 `action`。`action` 用 `review` 表示需要复核更新或新纳入的文档，`remove` 表示该文档已迁出原项目。状态应能保存成 JSON，换一个应用实例后继续使用。具体实现、内部函数、过滤方法和调用次数由学员自行决定。

项目归属与正文版本独立变化。同一正文版本迁出项目仍要撤出原依据，迁回项目仍要重新纳入；不能只按版本递增决定是否通知。

先基于资料形成 Spec，说明本次范围、历史要求、采用的资料版本与验收；然后实现并检查。不能把“代码已写完”当作项目完成。
