"""实际启动 HTTP 服务与 stdio MCP，核对跨系统资料、版本与失败返回。"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from threading import Thread

from mcp import Client, StdioServerParameters
from enterprise_fixture import EnterpriseFixture, create_server, prepare_repository

HERE = Path(__file__).resolve().parent
LAB = HERE.parent


async def probe(base: str, output: Path):
    env = {key: value for key, value in os.environ.items() if not any(part in key.upper() for part in ["TOKEN", "SECRET", "PASSWORD", "API_KEY"])}
    env.update({"JIRA_BASE_URL": base, "WIKI_BASE_URL": base, "GITLAB_BASE_URL": base,
                "CONTEXT_FETCH_LOG": str(output / "http-fetch.jsonl")})
    target = StdioServerParameters(command=sys.executable, args=[str(HERE / "context_mcp.py")], env=env)
    trace = []
    async with Client(target) as client:
        tools = await client.list_tools()
        expected = {"jira_get_issue", "wiki_search_pages", "wiki_read_page", "gitlab_read_file", "gitlab_read_mr"}
        assert {tool.name for tool in tools.tools} == expected
        for tool in tools.tools:
            hints = tool.annotations.model_dump(by_alias=True, exclude_none=True)
            assert hints == {"readOnlyHint": True, "destructiveHint": False,
                             "idempotentHint": True, "openWorldHint": True}
        (output / "tools-list.json").write_text(json.dumps(tools.model_dump(by_alias=True, exclude_none=True), ensure_ascii=False, indent=2))

        async def call(name, arguments, error=False):
            result = await client.call_tool(name, arguments)
            trace.append({"tool": name, "arguments": arguments, "result": result.model_dump(by_alias=True, exclude_none=True)})
            assert bool(result.is_error) == error, trace[-1]
            return result.structured_content

        issue = await call("jira_get_issue", {"issue_key": "KNOW-201"})
        assert issue["data"]["key"] == "KNOW-201"
        pages = await call("wiki_search_pages", {"query": "", "project_key": "atlas"})
        assert {row["id"] for row in pages["data"]["results"]} == {"100", "101", "102"}
        source_versions = {}
        for row in pages["data"]["results"]:
            page = await call("wiki_read_page", {"page_id": row["id"], "version": row["version"]["number"]})
            assert page["version"]["number"] == row["version"]["number"]
            assert page["data"]["body"]["storage"]["value"]
            source_versions[page["id"]] = page["version"]["number"]
        sdk = await call("gitlab_read_file", {"project_id": 42, "file_path": "shared/wiki_sdk.py", "ref": "HEAD"})
        commit = sdk["version"]["commit"]
        assert len(commit) == 40 and len(sdk["version"]["blob"]) == 40
        content = sdk["data"]["text"].encode()
        blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        assert blob == sdk["version"]["blob"]
        app = await call("gitlab_read_file", {"project_id": 42, "file_path": "src/application.py", "ref": commit})
        assert app["version"]["commit"] == commit
        mr = await call("gitlab_read_mr", {"project_id": 42, "mr_iid": 18})
        assert mr["data"]["state"] == "merged"
        # 页面不存在与版本不存在必须成为 MCP 工具失败，不能回报已读取。
        await call("wiki_read_page", {"page_id": "9999"}, error=True)
        await call("wiki_read_page", {"page_id": "100", "version": 9999}, error=True)
        await call("gitlab_read_file", {"project_id": 42, "file_path": "../../private.txt", "ref": commit}, error=True)
        result = {"passed": True, "mode": "real-stdio-mcp-to-loopback-http", "model_called": False,
                  "protocol": client.protocol_version, "tool_count": len(tools.tools),
                  "calls": len(trace), "successful_calls": sum(not row["result"].get("isError", False) for row in trace),
                  "wiki_versions": source_versions, "git_commit": commit,
                  "sdk_blob_verified": True, "readonly_annotations_verified": True, "trace": trace}
        (output / "mcp-trace.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=LAB / "artifacts/integration-probe")
    parser.add_argument("--repo-root", type=Path, default=LAB / "starter")
    args = parser.parse_args()
    assert shutil.disk_usage(HERE).free >= 384 * 1024**2, "磁盘不足 384 MiB，停止"
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        raise SystemExit("输出目录已有记录，请换一个新目录。")
    fixture = EnterpriseFixture(prepare_repository(args.repo_root), args.out / "http-server.jsonl")
    server = create_server("127.0.0.1", 0, fixture)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        result = asyncio.run(probe(f"http://127.0.0.1:{server.server_port}", args.out))
        received = [json.loads(line) for line in (args.out / "http-server.jsonl").read_text().splitlines()]
        sent = [json.loads(line) for line in (args.out / "http-fetch.jsonl").read_text().splitlines()]
        assert len(received) == result["calls"]
        assert len(sent) == result["successful_calls"]
        assert sum(row["status"] == 404 for row in received) == 3
        assert {r["response_sha256"] for r in sent} <= {r["response_sha256"] for r in received}
        summary = {key: value for key, value in result.items() if key != "trace"}
        summary.update(http_requests_received=len(received), failures_preserved=3,
                       actual_http_response_hashes_match=True)
        (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
        print(json.dumps(summary, ensure_ascii=False))
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == "__main__":
    main()
