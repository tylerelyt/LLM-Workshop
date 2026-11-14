"""Authorize Feishu in an interactive terminal and list visible documents."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile


SEARCH_SCOPE = "search:docs:read"


def workspace_environment():
    environment = os.environ.copy()
    for name in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY"):
        environment.pop(name, None)
    environment["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    environment["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    return environment


def run_lark(arguments, environment, *, timeout=45):
    try:
        result = subprocess.run(["lark-cli", *arguments], env=environment,
                                capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise RuntimeError("lark-cli is not on PATH. Install the Feishu CLI first.") from None
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"lark-cli did not respond within {timeout} seconds.") from None
    except OSError as error:
        raise RuntimeError(f"Could not start lark-cli: {error.strerror}") from None

    raw = (result.stderr or result.stdout) if result.returncode else result.stdout
    try:
        payload = json.loads(raw)
    except ValueError:
        raise RuntimeError(f"lark-cli did not return JSON (exit {result.returncode}).") from None
    if result.returncode or payload.get("ok") is False:
        error = payload.get("error", {})
        message = error.get("message") or f"lark-cli failed (exit {result.returncode})."
        missing_scopes = error.get("missing_scopes", [])
        if missing_scopes:
            message += " Missing scopes: " + ", ".join(missing_scopes)
        raise RuntimeError(message)
    return payload


HIGHLIGHT = re.compile(r"</?hb?>", re.IGNORECASE)


def search_documents(query, page_size, page_token, environment):
    command = ["drive", "+search", "--as", "user", "--doc-types", "docx,doc,wiki",
               "--query", query, "--page-size", str(page_size)]
    if page_token:
        command += ["--page-token", page_token]
    payload = run_lark(command, environment)
    if payload.get("ok") is not True or payload.get("identity") != "user":
        raise RuntimeError("飞书未确认这是一次成功的用户身份搜索。")
    page = payload.get("data", {})
    results = page.get("results")
    if not isinstance(results, list):
        raise RuntimeError("飞书响应缺少文档列表。")

    documents = []
    for item in results:
        title = item.get("title") or item.get("title_highlighted") or "未命名"
        documents.append({
            "title": " ".join(HIGHLIGHT.sub("", title).split()),
            "url": item.get("url") or "",
            "doc_type": item.get("doc_type") or item.get("type") or "文档",
        })
    return {
        "documents": documents,
        "has_more": bool(page.get("has_more")),
        "next_page_token": page.get("page_token") or None,
    }


def authorize(environment):
    payload = run_lark(["auth", "login", "--scope", SEARCH_SCOPE, "--no-wait", "--json"], environment)
    data = payload.get("data", payload)
    url = data.get("verification_url") or data.get("verification_uri_complete")
    device_code = data.get("device_code")
    if not url or not device_code:
        raise RuntimeError("飞书未返回扫码授权链接或设备码。")

    # The user sees the URL and QR path before the local process starts polling.
    with tempfile.TemporaryDirectory(prefix="feishu-auth-") as directory:
        qr_dir = Path(directory)
        qr_file = qr_dir / "authorize.png"
        try:
            subprocess.run(["lark-cli", "auth", "qrcode", url, "--output", qr_file.name],
                           cwd=qr_dir, env=environment, capture_output=True, check=True, timeout=20)
        except (subprocess.SubprocessError, OSError):
            raise RuntimeError("未能生成授权二维码。") from None
        print(f"请打开授权链接，或用飞书扫描二维码。\n{url}\n二维码图片 {qr_file}", flush=True)
        if sys.platform == "darwin" and sys.stdout.isatty():
            try:
                subprocess.run(["open", str(qr_file)], capture_output=True, timeout=5)
            except (subprocess.SubprocessError, OSError):
                pass  # The QR path and authorization URL are already visible.
        timeout = min(int(data.get("expires_in", 600)) + 10, 900)
        run_lark(["auth", "login", "--device-code", device_code, "--json"], environment, timeout=timeout)


def request_authorization(args, environment):
    if not args.list_only:
        authorize(environment)
        print("扫码授权已完成。", flush=True)


def request_via_cli(args, environment):
    request_authorization(args, environment)
    print("直接运行 lark-cli drive +search。", flush=True)
    return search_documents(args.query, args.limit, args.page_token, environment)


def print_documents(page, args, script=None):
    documents = page["documents"]
    print(f"本页找到 {len(documents)} 条飞书文档。")
    for index, document in enumerate(documents, 1):
        url = document["url"]
        print(f"{index}. [{document['doc_type']}] {document['title']}" + (f"  {url}" if url else ""))
    if page["has_more"] and page["next_page_token"]:
        next_page = [sys.executable, str(script or Path(__file__).resolve()), "--list-only",
                     "--query", args.query, "--limit", str(args.limit),
                     "--page-token", page["next_page_token"]]
        if getattr(args, "via", None):
            next_page += ["--via", args.via]
        print(f"还有更多结果。\n{shlex.join(next_page)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
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
        page = request_via_cli(args, environment)
        print_documents(page, args)
    except RuntimeError as error:
        parser.exit(1, f"飞书文档查找失败。{error}\n")


if __name__ == "__main__":
    main()
