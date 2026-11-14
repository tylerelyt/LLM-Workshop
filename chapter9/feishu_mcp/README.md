# 飞书远程 MCP

<a id="remote-mcp"></a>

本练习的目标是使用已获授权的用户身份发现飞书托管 MCP 的文档搜索工具，构造符合其参数结构的查询，并用真实响应确认一份教学文档。

## 工程任务

远程工具有自己的凭证与访问权限，连接成功不代表能读取目标文档。

在 [remote_feishu_mcp.py](remote_feishu_mcp.py) 中，固定账号和文档权限，只改变远程工具发布 schema 中的搜索关键词参数。

分别核对身份、schema 和真实文档结果，说明故障发生在认证、参数还是内容访问。

## 准备一份可以核对的文档

准备 Python 3.11 或 3.12、飞书自建应用及其用户授权。选定一份当前账号有权查看、标题容易识别的教学 Doc 或 Docx，先在飞书中记录它的标题和链接。学习目标是完成真实搜索，凭据缺失属于运行前提尚未满足。

以下命令从仓库根目录运行。了解 MCP 的发现与调用过程即可独立完成本练习，无需其他课的结果文件。[MCP 基础](../mcp_tools/README.md)

```bash
python -m pip install -r chapter9/feishu_mcp/requirements.txt
mkdir -p chapter9/feishu_mcp/results
```

1. 自建应用开启 `search:docs:read` 和 `wiki:wiki:readonly` 两项用户权限，确认测试用户在应用可用范围内。[飞书远程 MCP 开发文档](https://open.feishu.cn/document/mcp_open_tools/developers-call-remote-mcp-server)
2. 配置 OAuth 回调地址，用测试用户授予上述权限，将授权码换成 `user_access_token`。[获取授权码](https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code) · [获取用户访问凭证](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/authentication-management/access-token/get-user-access-token)
3. 执行 `read` 后输入凭证并回车，终端不会显示输入。保持凭证在本机环境变量里。

```bash
read -rs FEISHU_MCP_UAT
export FEISHU_MCP_UAT
python chapter9/feishu_mcp/remote_feishu_mcp.py \
  > chapter9/feishu_mcp/results/search-schema.json
```

客户端将凭证放入 `X-Lark-MCP-UAT` 请求头，连接 `https://mcp.feishu.cn/mcp`，只请求发布 `search-doc`。打开保存的参数结构，确认请求成功后再构造搜索输入。这是本例所选飞书托管服务的接入方式，授权流程与部署服务相关。

## 只改变搜索关键词

根据真实发现的参数结构创建 `chapter9/feishu_mcp/results/search-a.json`，搜索目标教学文档的关键词。可以请 Coding Agent 按这份结构生成 JSON，学员核对字段、类型和实际关键词。只编辑自己的查询文件，保留服务地址、权限要求和客户端实现。

```bash
python chapter9/feishu_mcp/remote_feishu_mcp.py \
  --arguments "$(cat chapter9/feishu_mcp/results/search-a.json)" \
  > chapter9/feishu_mcp/results/search-a-result.json
```

打开结果，核对目标文档的标题和链接与飞书中记录的一致。再复制查询为 `search-b.json`，只改变关键词，保持账号、权限、其他过滤条件和返回数量不变。

```bash
python chapter9/feishu_mcp/remote_feishu_mcp.py \
  --arguments "$(cat chapter9/feishu_mcp/results/search-b.json)" \
  > chapter9/feishu_mcp/results/search-b-result.json
```

运行前预测结果是否会变，运行后解释出现、消失或保留的文档。查询成功但没有命中时，结合关键词和过滤条件检查，不把“能发现工具”当作已找到目标文档。

## 独立验收与状态

保留参数结构、两份查询与两份响应，至少一次真实找到事先选定的教学文档。说明哪一层负责身份授权、哪一层发现工具、哪一层执行搜索。材料中去除用户凭证、授权码和设备码。

真实搜索完成后，可以诊断缺少凭证的路径。

```bash
env -u FEISHU_MCP_UAT python chapter9/feishu_mcp/remote_feishu_mcp.py
```

该命令只移除本次进程的变量，不撤销飞书授权。缺少变量时应在客户端启动阶段停止。凭证过期或权限不足时，分别处理用户授权和应用权限后重试。结束后可 `unset FEISHU_MCP_UAT`，并只清理本课自己生成的查询和结果文件。

本地模拟可验证请求头、参数与协议，真实权限和真实文档命中仍由上面的飞书运行验收。[CLI 技能](../cli_skills/README.md) · [主题目录](../README.md)

## 在自己的项目中使用

选择当前账号确实可见的一份文档，以标题与链接作为外部核对依据。再独立完成[CLI Skill](../cli_skills/README.md)，固定账号与关键词比较授权准备、实际调用和返回范围，依据运行环境选择接入方式。
