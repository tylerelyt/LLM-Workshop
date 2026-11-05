"""把 Jira、Confluence 与 GitLab 的只读 HTTP API 接入 MCP。"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel

mcp = MCPServer(
    "project-context",
    instructions="本服务提供研发调查所需的需求、Wiki 与代码。保留来源 ID、版本和链接；读取结果不是完成研发任务。",
    version="1.0.0",
)

# 描述五项工具实际的 GET 行为，不代替 Host 审批或企业 API 的权限校验。
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True,
)


def component(value: str) -> str:
    return quote(str(value), safe="")


def auth_headers(system: str) -> dict[str, str]:
    """凭据只放请求头，不放工具参数、返回正文或日志。"""
    headers = {"Accept": "application/json"}
    if system == "gitlab":
        if token := os.environ.get("GITLAB_TOKEN"):
            headers["PRIVATE-TOKEN"] = token
    elif token := os.environ.get(f"{system.upper()}_BEARER_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    elif (email := os.environ.get(f"{system.upper()}_EMAIL")) and (token := os.environ.get(f"{system.upper()}_API_TOKEN")):
        encoded = base64.b64encode(f"{email}:{token}".encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"
    return headers


def fetch_json(system: str, path: str, params: dict | None = None) -> tuple[dict, str]:
    base = os.environ.get(f"{system.upper()}_BASE_URL", "http://127.0.0.1:8766").rstrip("/")
    url = base + path + (("?" + urlencode(params)) if params else "")
    request = Request(url, headers=auth_headers(system), method="GET")
    try:
        # 真正的 HTTP 调用发生在这里；隔离课堂服务与企业服务使用同一条路径。
        with urlopen(request, timeout=10) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ToolError("接口响应过大，请缩小查询范围。")
            status = response.status
            data = json.loads(raw)
    except HTTPError as error:
        raise ToolError(f"{system} API 返回 HTTP {error.code}，请核对对象编号、权限和版本。") from error
    except URLError as error:
        raise ToolError(f"{system} API 连接失败，请核对服务地址与网络。") from error
    if target := os.environ.get("CONTEXT_FETCH_LOG"):
        record = {"system": system, "method": "GET", "url": url, "status": status,
                  "response_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        destination = Path(target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return data, url


class ContextResult(BaseModel):
    source: str
    id: str
    version: dict[str, Any]
    url: str
    retrieved_at: str
    data: dict[str, Any]


def result(source: str, identity: str, version: dict, url: str, data: dict) -> ContextResult:
    return ContextResult(source=source, id=str(identity), version=version, url=url,
                         retrieved_at=datetime.now(timezone.utc).isoformat(), data=data)


@mcp.tool(structured_output=True, annotations=READ_ONLY)
def jira_get_issue(issue_key: str) -> ContextResult:
    """读取 Jira 工单的需求、状态、更新时间与关联资料；从工单开始研发调查。"""
    data, url = fetch_json("jira", "/rest/api/3/issue/" + component(issue_key),
                           {"fields": "summary,description,status,updated,issuelinks,labels"})
    return result("jira", data["key"], {"updated": data["fields"]["updated"]}, url, data)


def cql_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


@mcp.tool(structured_output=True, annotations=READ_ONLY)
def wiki_search_pages(query: str, project_key: str) -> ContextResult:
    """按项目标签和关键词查找 Wiki 页面，返回页面 ID、版本及链接；正文再按 ID 读取。"""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", project_key):
        raise ToolError("project_key 使用小写字母、数字、下划线或短横线。")
    cql = f'type = page AND label = {cql_string("project-" + project_key)}'
    if query:
        cql += " AND text ~ " + cql_string(query)
    data, url = fetch_json("wiki", "/wiki/rest/api/content/search",
                           {"cql": cql, "expand": "version,metadata.labels", "limit": 25})
    return result("wiki-search", project_key, {}, url, data)


@mcp.tool(structured_output=True, annotations=READ_ONLY)
def wiki_read_page(page_id: str, version: int | None = None) -> ContextResult:
    """按页面 ID 读取 Wiki 正文；需要复核历史依据时明确给出版本号。"""
    params: dict = {"body-format": "storage"}
    if version is not None:
        if version < 1:
            raise ToolError("页面版本从 1 开始。")
        params["version"] = version
    data, url = fetch_json("wiki", "/wiki/api/v2/pages/" + component(page_id), params)
    return result("wiki", data["id"], {"number": data["version"]["number"]}, url, data)


@mcp.tool(structured_output=True, annotations=READ_ONLY)
def gitlab_read_file(project_id: int, file_path: str, ref: str) -> ContextResult:
    """按 GitLab 项目、路径和 ref 读取文件，保留真实 commit/blob 标识并解码正文。"""
    data, url = fetch_json("gitlab", f"/api/v4/projects/{project_id}/repository/files/{component(file_path)}", {"ref": ref})
    if data.get("encoding") != "base64":
        raise ToolError("GitLab 文件编码不是 base64，请检查接口配置。")
    data["text"] = base64.b64decode(data["content"], validate=True).decode("utf-8")
    return result("gitlab-file", f"{project_id}:{data['file_path']}",
                  {"commit": data["commit_id"], "blob": data["blob_id"]}, url, data)


@mcp.tool(structured_output=True, annotations=READ_ONLY)
def gitlab_read_mr(project_id: int, mr_iid: int) -> ContextResult:
    """读取历史合并请求的说明、状态与提交，用于还原已经采用的设计决定。"""
    data, url = fetch_json("gitlab", f"/api/v4/projects/{project_id}/merge_requests/{mr_iid}")
    return result("gitlab-mr", f"{project_id}!{mr_iid}", {"sha": data["sha"]}, url, data)


if __name__ == "__main__":
    mcp.run(transport="stdio")
