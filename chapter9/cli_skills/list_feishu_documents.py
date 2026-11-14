"""Ask for Feishu authorization, then list documents through CLI or stdio MCP."""

import argparse
import asyncio
from pathlib import Path
import sys

if __package__:
    from . import check_feishu_access
else:
    import check_feishu_access

from search_documents import print_documents, request_authorization, request_via_cli, workspace_environment


TOOL_NAME = "search_feishu_documents"


async def request_via_mcp(args, environment):
    try:
        from mcp import StdioServerParameters
        from mcp.client import Client
    except ImportError:
        raise RuntimeError("请先用课程 Python 环境安装 mcp==2.3.0。") from None

    server_script = Path(__file__).with_name("feishu_mcp_server.py").resolve()
    server = StdioServerParameters(command=sys.executable, args=[str(server_script)], env=environment)
    async with Client(server) as client:
        tools = (await client.list_tools()).tools
        if TOOL_NAME not in {tool.name for tool in tools}:
            raise RuntimeError("MCP 服务未发布飞书文档搜索工具。")
        print(f"MCP 已连接，发现工具 {TOOL_NAME}。", flush=True)
        await asyncio.to_thread(request_authorization, args, environment)
        print(f"通过 MCP 调用 {TOOL_NAME}。", flush=True)
        result = await client.call_tool(TOOL_NAME, {
            "query": args.query, "page_size": args.limit, "page_token": args.page_token,
        })
        if result.is_error:
            detail = next((item.text for item in result.content if item.type == "text"), "MCP 工具调用失败。")
            raise RuntimeError(detail)
        if not result.structured_content:
            raise RuntimeError("MCP 工具未返回结构化文档列表。")
        return result.structured_content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--via", choices=("cli", "mcp"), default="mcp", help="Choose the integration path")
    parser.add_argument("--query", default="", help="Search keyword, up to 30 characters")
    parser.add_argument("--limit", type=int, default=10, choices=range(1, 21), metavar="1-20")
    parser.add_argument("--list-only", action="store_true", help="Use the current authorization")
    parser.add_argument("--page-token", help="Page token returned by the previous search")
    args = parser.parse_args()
    if len(args.query) > 30:
        parser.error("--query must contain at most 30 characters.")
    if args.page_token and not args.list_only:
        parser.error("--page-token requires --list-only.")
    environment = workspace_environment()

    try:
        print("正在查找当前账号可见的飞书文档。", flush=True)
        if args.via == "cli":
            page = request_via_cli(args, environment)
        else:
            page = asyncio.run(request_via_mcp(args, environment))
        print_documents(page, args, script=Path(__file__).resolve())
    except RuntimeError as error:
        parser.exit(1, f"飞书文档查找失败。{error}\n")


if __name__ == "__main__":
    main()
