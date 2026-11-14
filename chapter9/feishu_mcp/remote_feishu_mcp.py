"""Connect to Feishu Remote MCP using a user access token obtained in advance."""

import argparse
import asyncio
import json
import os

import httpx2
from mcp import MCPError
from mcp.client import Client
from mcp.client.streamable_http import streamable_http_client


ENDPOINT = "https://mcp.feishu.cn/mcp"
TOOL = "search-doc"


def failure_message(error):
    if isinstance(error, ExceptionGroup):
        # The transport wraps request errors in nested task groups.
        for cause in error.exceptions:
            message = failure_message(cause)
            if message:
                return message
    elif isinstance(error, MCPError):
        if error.code in (-32003, -32010, -32011):
            return "飞书未接受用户凭证。请重新获取 user_access_token，再设置 FEISHU_MCP_UAT。"
        if error.code == -32602:
            return "飞书不接受本次工具参数。请先不带 --arguments 运行，查看 search-doc 的参数结构。"
    elif isinstance(error, httpx2.HTTPStatusError):
        if error.response.status_code == 401:
            return "飞书未接受用户凭证。请重新获取 user_access_token，再设置 FEISHU_MCP_UAT。"
        if error.response.status_code == 403:
            return "飞书拒绝访问。请核对应用可用范围和 search:docs:read、wiki:wiki:readonly 权限。"
    elif isinstance(error, httpx2.RequestError):
        return "无法连接飞书远程 MCP。请检查到 mcp.feishu.cn 的网络后重试。"
    elif isinstance(error, RuntimeError):
        return str(error)
    return None


async def run(token, arguments):
    headers = {"X-Lark-MCP-UAT": token, "X-Lark-MCP-Allowed-Tools": TOOL}
    async with httpx2.AsyncClient(headers=headers, timeout=30) as http:
        transport = streamable_http_client(ENDPOINT, http_client=http)
        async with Client(transport, mode="legacy", read_timeout_seconds=30) as client:
            tools = (await client.list_tools()).tools
            search = next((tool for tool in tools if tool.name == TOOL), None)
            if search is None:
                raise RuntimeError("飞书远程 MCP 没有发布 search-doc，请检查应用权限和 token。")
            if arguments is None:
                print(json.dumps(search.input_schema, ensure_ascii=False, indent=2))
                return
            result = await client.call_tool(TOOL, arguments)
            if result.is_error:
                raise RuntimeError("search-doc 调用失败，请检查当前工具 schema 和文档搜索权限。")
            content = result.structured_content
            if content is None:
                content = [item.text for item in result.content if item.type == "text"]
            print(json.dumps(content, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arguments", help="JSON object matching the published search-doc schema")
    args = parser.parse_args()
    token = os.environ.get("FEISHU_MCP_UAT")
    if not token:
        parser.error("请先在飞书开放平台取得 user_access_token，再设置 FEISHU_MCP_UAT。")
    arguments = None
    if args.arguments is not None:
        try:
            arguments = json.loads(args.arguments)
        except json.JSONDecodeError:
            parser.error("--arguments 必须是有效的 JSON 对象。")
        if not isinstance(arguments, dict):
            parser.error("--arguments 必须是 JSON 对象。")
    try:
        asyncio.run(run(token, arguments))
    except Exception as error:
        message = failure_message(error) or "无法完成飞书远程 MCP 请求。请检查凭证、应用权限和网络。"
        parser.exit(1, f"{message}\n")


if __name__ == "__main__":
    main()
