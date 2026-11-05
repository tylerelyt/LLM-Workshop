# 企业上下文 Workshop：用 MCP、Skill 和 Spec 完成存量研发

给已有知识平台增加项目检索和文档变更订阅。起始应用已经能完成全局检索；本次需要接入企业资料，查清已采用的设计和兼容要求，再形成 Spec、实施和验证。完整要求见 [学员题面](ASSIGNMENT.md)。

## 启动练习

先按仓库根目录的 [DeepSeek 运行说明](../../README-DEEPSEEK.md) 安装环境并配置本机密钥。以下命令从仓库根目录执行。

终端 A 启动企业演示服务：

```bash
python workshops/enterprise_context/integration/enterprise_fixture.py
```

终端 B 启动 DeepSeek Flash：

```bash
python workshops/enterprise_context/harness/run_deepseek.py \
  --out workshops/enterprise_context/runs/flash-001
```

宿主在新输出目录中复制起始应用和项目 Skill。模型先获得 Skill 的名称和简介，再通过文件工具按需读取正文和模板；通过真实 stdio MCP 读取 Jira、Wiki、GitLab，之后编写 Spec 和应用代码。模型的文件工具只能读当前工作副本，不能读取讲师答案；共享 SDK 不可写。

服务中的企业资料是教学构造，MCP 与 HTTP 请求是真实执行。GitHub 源码包不携带嵌套 Git 仓库，服务会在本模块的运行目录中建立独立 Git 快照，供演示 GitLab 文件接口读取。不会向线上系统写入工单、评论或代码。

## 检查结果

在指定输出目录中查看：

- `workspace/specs/KNOW-201/spec.md`：模型形成的规格及其采用的资料。
- `workspace/src/application.py`：模型实际完成的应用修改。
- `business-check.json`：兼容、项目隔离、事件去重、实例恢复和文档迁移的独立检查。
- `summary.json`：真实 API usage、模型完成情况、Spec 与共享 SDK 检查。
- `answer.md`：模型对结果的说明。

模型可以调用业务检查获取反馈；宿主结束时还会再次独立执行检查。不能只看模型的完成声明，也不能用文件存在代替业务结果。原始 `events.jsonl` 留在本机供复核，不随学员包分发。

只核对协议连通、不调用模型时：

```bash
python workshops/enterprise_context/integration/client_probe.py \
  --out workshops/enterprise_context/runs/protocol-check
```

运行目录不能覆盖已有记录。重做时换一个新目录；企业服务终端按 Ctrl-C 停止。接入实际企业时，再按 [API 适配说明](integration/README.md) 替换地址、认证和部署接口。Wiki 业务变更订阅与 MCP 资源订阅是两种不同机制。
