# CLI Skill 与扫码授权

<a id="cli-skill"></a>

运行一个 Python 脚本，完成飞书扫码授权并输出文档标题和链接。先把命令调通，再将同一脚本交给 Agent 使用，观察 CLI 与 Skill 各自承担什么工作。

## 先扫码，再搜索

需要 Python 3，以及已完成应用配置的 `lark-cli`。先按[飞书 CLI 安装与应用配置](https://github.com/larksuite/cli#readme)准备应用和文档权限。这个搜索脚本不调用聊天模型，也不需要远程 MCP 凭证。

选一份当前账号可见、标题容易核对的文档，把关键词换成标题的一部分。从仓库根目录运行：

```bash
python3 chapter9/cli_skills/skills/feishu-document-search/scripts/search_documents.py \
  --query '教学文档关键词'
```

程序显示授权链接和二维码图片路径。用飞书扫码确认后，它以用户身份执行 `lark-cli drive +search`，输出标题和链接。核对返回结果与飞书中的目标文档是否一致。

二维码位于临时目录，授权等待结束后会被清理；用户凭据由 CLI 保存。能完成扫码与能读取目标文档分别检查，查询成功但没有命中时，再检查关键词、账号和可见范围。

<a id="先运行脚本再复用授权"></a>

## 复用授权，观察分页

保持账号和关键词不变，再次运行：

```bash
python3 chapter9/cli_skills/skills/feishu-document-search/scripts/search_documents.py \
  --list-only --query '教学文档关键词'
```

`--list-only` 复用当前授权，不启动扫码流程。确认两次返回的目标标题与链接一致；省略 `--query` 可以浏览当前账号可见的文档。

脚本默认返回一页、每页 10 条；有后续页时会显示下一页命令。固定关键词，把 `--limit` 改成 `3`，检查每页数量及下一页结果。关键词最多 30 个字符，页大小为 1—20。

<a id="把同一个脚本交给技能"></a>

## 让 Agent 使用同一个脚本

这一阶段需要能加载 Agent Skills 并执行本地命令的运行框架。脚本的授权和搜索逻辑继续复用，模型使用该框架的配置。

阅读[技能说明](skills/feishu-document-search/SKILL.md)，将整个 `feishu-document-search` 目录安装到自己的框架，保留相对路径。新建会话，要求按相同关键词搜索并复用授权，然后检查：

- 实际命令是否调用本技能的脚本，是否带有 `--list-only`。
- CLI 返回的标题、链接与 Agent 展示的结果是否对应。
- 授权失败、搜索失败和没有命中时，Agent 是否如实说明。

复制一份技能说明，只改变结果呈现要求，例如按“标题、链接”两列展示。用新会话重问，比较说明变化是否影响呈现，真实查询和文档结果是否仍可核对。每轮只改说明中的一项，保留脚本与权限要求。

<a id="与-mcp-的横向对照"></a>

## 与远程 MCP 比较

用同一个账号和关键词，独立运行[飞书远程 MCP](../feishu_mcp/README.md)。两条路径分别完成授权和查询，再比较准备工作、实际调用与返回范围：

| 对照项 | 本例飞书远程 MCP | 本例 CLI Skill |
| --- | --- | --- |
| 接入准备 | 应用权限、用户凭证、远程地址与请求头 | 本机 CLI、应用配置与扫码入口 |
| 凭据管理 | 客户端连接前取得并管理凭证 | CLI 完成扫码、保存并复用凭据 |
| 操作方式 | MCP 客户端发现结构并发送调用 | 技能说明用途，Agent 执行脚本 |
| 使用场景 | 多个 MCP 客户端连接同一套远程工具 | 本机命令编排、独立调试和脚本复用 |

授权体验取决于这里使用的服务与实现。CLI 操作也可以包装成 MCP 工具：安装协议依赖后，复用同一套用户授权运行本地 MCP 路径。

```bash
python -m pip install -r chapter9/cli_skills/requirements.txt
python chapter9/cli_skills/list_feishu_documents.py \
  --via mcp --list-only --query '教学文档关键词'
```

这条命令使用本地 stdio MCP 和本机 CLI 身份，与远程 MCP 服务分别运行。模拟 CLI 响应只能检查程序分支；真实权限与目标文档命中需要用实际账号确认。

## 用到自己的操作流程

选择一个高频只读操作，先调通脚本输入、输出和授权复用，再封装技能。固定任务，在独立会话中比较实际调用。需要观察 SDK 怎样加载技能、管理会话和读取文档时，继续看[Pi SDK](../pi_skills/README.md)。

实验后恢复修改过的技能说明，只清理自己的本地记录；授权状态由 CLI 配置维护。

[主题目录](../README.md) · [全部练习](../../README.md#练习索引)
