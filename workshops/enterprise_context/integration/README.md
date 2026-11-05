# 把企业上下文接进 Harness

本目录提供真实的 stdio MCP 服务和 HTTP 适配器。课堂使用的 Jira、Wiki、GitLab 是本机隔离服务，资料为课程构造；请求真正经过 HTTP，不用内存中的预置返回冒充 API 调用。初始应用仍须由学员完成项目检索与变更订阅。

## 现场启动

在 `lab` 目录创建或复用 Python 环境，安装本目录的 `requirements.txt`。课程开发机已经有兼容环境，可直接复用，不必重复安装。

```sh
python integration/enterprise_fixture.py --port 8766
```

浏览器打开 `http://127.0.0.1:8766/`，先看 KNOW-201 工单、三份 atlas 项目资料、borealis 同名文档、已有代码和历史评审。HTTP 请求记录写在 `artifacts/http-requests.jsonl`。关闭这个终端或按 Ctrl-C 即停止服务。

另一个终端设置 API 地址，启动 MCP 服务。它的 stdout 是协议通道，不用于打印调试信息。

```sh
export JIRA_BASE_URL=http://127.0.0.1:8766
export WIKI_BASE_URL=http://127.0.0.1:8766
export GITLAB_BASE_URL=http://127.0.0.1:8766
python integration/context_mcp.py
```

通常由 Harness 的 MCP 配置启动第二个进程，不需要手工启动它；前一个 HTTP 服务则要保持运行。将这个命令及三个环境变量写入当前项目配置即可，具体 Harness 配置由课程的 `harness` 目录提供。

## 先检查接通，再让模型调查

```sh
python integration/client_probe.py --out artifacts/integration-probe-01
```

此命令会启动一个临时 HTTP 服务，使用官方 MCP Client 启动 stdio 子进程并发现五个工具；随后读取工单、搜索项目资料、按版本读正文、读取固定提交上的 SDK 和应用代码、读取历史 MR。它还核对不存在的页面、版本和路径确实返回失败。临时服务会自行关闭。

输出目录中的 `tools-list.json`、`mcp-trace.json`、`http-fetch.jsonl` 与 `http-server.jsonl` 分别记录工具定义、协议返回、发出的 HTTP 请求及服务端实收请求。GitLab 文件的 blob SHA 根据返回正文重新计算，并与 Git 对象比对。`model_called: false` 明确表示这个检查没有调用模型，不能冒充模型已经完成任务；课堂还需查看后续真实模型运行。

## 工具返回中保留什么

五个工具分别是 `jira_get_issue`、`wiki_search_pages`、`wiki_read_page`、`gitlab_read_file`、`gitlab_read_mr`。返回统一保留 `source`、`id`、`version`、`url`、`retrieved_at`、`data`。文件读取的 `ref` 可以先用分支取得当前完整提交，再用该提交读取其他文件。Wiki 页面按 `page_id` 与 `version` 共同标识依据。

这五项工具只发 GET 请求，工具定义如实声明 `readOnlyHint: true`、`destructiveHint: false`、`idempotentHint: true`。它们仍然访问外部系统，因此 `openWorldHint: true`。这些注解帮助 Host 识别工具语义，不代替 Host 的审批规则或企业 API 的访问权限。课堂如需预先批准，应只针对这五个已核实的只读工具配置，不能把所有未知工具一并批准。

项目过滤不是把标题里带有 atlas 的文档算作本项目。课堂资料使用项目标签与项目字段表达归属；同名的 borealis 资料用于检查范围。文档变更订阅属于应用读取业务事件后的处理，不是 MCP 的资源订阅功能。

## 换成实际企业系统

本例的读取路径对应 Jira Cloud REST v3、Confluence Cloud CQL 搜索及 REST v2 页面读取、GitLab REST v4。实际环境需要确认产品部署版本、项目标签约定与可读范围，再替换三个 `*_BASE_URL`。地址为站点根地址，不重复添加 `/api/v4` 或 `/wiki`。

- Jira / Wiki 的 OAuth 访问令牌使用 `JIRA_BEARER_TOKEN` / `WIKI_BEARER_TOKEN`。
- 使用 Atlassian 邮箱与 API Token 时，分别设置 `JIRA_EMAIL`、`JIRA_API_TOKEN` 或 `WIKI_EMAIL`、`WIKI_API_TOKEN`，适配器形成 Basic 请求头。
- GitLab 个人访问令牌使用 `GITLAB_TOKEN`，适配器形成 `PRIVATE-TOKEN` 请求头。

凭据通过环境变量交给进程，不写入 Skill、工具参数或课堂截图。上述配置不是所有企业部署的通用适配保证；Data Center、自建 Wiki 或其他鉴权方式应在此读取适配器上调整。课堂未访问任何企业内网。

## 一手接口依据

- [Jira 读取工单](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/)
- [Confluence 按 CQL 搜索](https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content/)
- [Confluence v2 读取页面及指定版本](https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/)
- [GitLab 仓库文件](https://docs.gitlab.com/api/repository_files/)
- [GitLab 合并请求](https://docs.gitlab.com/api/merge_requests/)
