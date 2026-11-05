"""课程隔离 HTTP 服务：按真实 REST 形状提供固定教学资料，不连接任何企业。"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from threading import Lock
from urllib.parse import parse_qs, quote, unquote, urlsplit

HERE = Path(__file__).resolve().parent
LAB = HERE.parent


def adf(text: str) -> dict:
    return {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": line}]}
        for line in text.splitlines() if line]}


class EnterpriseFixture:
    def __init__(self, repo_root: Path, log_path: Path):
        self.repo_root, self.log_path = repo_root.resolve(), log_path.resolve()
        self.lock = Lock()

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(self.repo_root), *args], text=True,
                                       stderr=subprocess.DEVNULL).strip()

    def documents(self) -> list[dict]:
        return json.loads((self.repo_root / "data/wiki.json").read_text())["documents"]

    def record(self, record: dict):
        with self.lock:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def page(self, doc: dict) -> dict:
        return {"id": str(doc["page_id"]), "status": "current", "title": doc["title"],
                "spaceId": "10", "project_key": doc["project_key"],
                "version": {"number": doc["version"], "createdAt": "2026-10-31T01:00:00Z"},
                "body": {"storage": {"representation": "storage", "value": doc["body"]}},
                "_links": {"webui": "/wiki/spaces/KNOW/pages/" + str(doc["page_id"])}}

    def issue(self) -> dict:
        text = """为现有企业知识平台增加按项目检索与文档变更订阅。
业务目标：atlas 项目成员只查看本项目资料，并能收到本项目资料后续变化。
现状：全局关键词检索已经供旧调用方使用，必须继续兼容。
请先核对 Wiki 设计页100、历史评审101、当前API页102，以及 GitLab 项目42的共享SDK、应用代码和历史MR !18。
本轮修改范围为应用层检索、订阅编排与对应回归；共享 Wiki SDK 由多个应用使用，本轮不修改。
完成时交付 Spec、应用层代码、回归结果与资料版本依据。"""
        return {"id": "1201", "key": "KNOW-201", "fields": {
            "summary": "知识平台：按项目检索与文档变更订阅", "description": adf(text),
            "status": {"name": "待开发"}, "updated": "2026-10-31T01:00:00.000+0000",
            "labels": ["atlas"], "issuelinks": []}}

    def repository_file(self, file_path: str, ref: str) -> dict:
        pure = PurePosixPath(file_path)
        if pure.is_absolute() or ".." in pure.parts or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,160}", ref):
            raise ValueError("文件路径或 ref 不合法")
        commit = self.git("rev-parse", "--verify", ref + "^{commit}")
        data = subprocess.check_output(["git", "-C", str(self.repo_root), "show", commit + ":" + file_path],
                                       stderr=subprocess.DEVNULL)
        blob = self.git("rev-parse", commit + ":" + file_path)
        return {"file_name": pure.name, "file_path": file_path, "size": len(data), "encoding": "base64",
                "content_sha256": hashlib.sha256(data).hexdigest(), "ref": ref,
                "blob_id": blob, "commit_id": commit,
                "last_commit_id": self.git("log", "-1", "--format=%H", commit, "--", file_path),
                "content": base64.b64encode(data).decode()}

    def home(self) -> str:
        issue = self.issue()
        docs = self.documents()
        try:
            commit = self.git("rev-parse", "HEAD")
            files = self.git("ls-files").splitlines()
        except subprocess.CalledProcessError:
            commit, files = "仓库尚未初始化", []
        paragraphs = "".join("<p>" + escape(p["content"][0]["text"]) + "</p>" for p in issue["fields"]["description"]["content"])
        doc_rows = "".join(f'<tr><td><a href="/wiki/api/v2/pages/{d["page_id"]}?body-format=storage">{d["page_id"]}</a></td><td>{escape(d["title"])}</td><td>{escape(d["project_key"])}</td><td>{d["version"]}</td></tr>' for d in docs)
        file_rows = "".join(f'<li><a href="/api/v4/projects/42/repository/files/{quote(f, safe="")}?ref={commit}">{escape(f)}</a></li>' for f in files)
        return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>企业上下文 · 课程隔离服务</title>
<style>body{{font:21px/1.65 -apple-system,"PingFang SC",sans-serif;max-width:1120px;margin:36px auto;padding:0 28px;color:#252522}}h1{{font-size:35px;margin:0 0 10px}}h2{{font-size:26px;margin:30px 0 8px}}p{{margin:7px 0}}a{{color:#98512e}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;border-bottom:1px solid #dad6ce;padding:8px 15px 8px 0}}code{{font-size:17px}}small{{color:#67645e}}</style>
<h1>KNOW-201：给知识平台增加项目检索与变更订阅</h1>
<small>课程隔离服务；本地 HTTP 确实执行，资料为教学构造。</small>
<h2>Jira 工单 · {escape(issue["fields"]["status"]["name"])}</h2>{paragraphs}
<h2>Wiki 资料与版本</h2><table><tr><th>页面</th><th>标题</th><th>项目</th><th>版本</th></tr>{doc_rows}</table>
<h2>GitLab 项目 42 · 已有代码</h2><p><code>提交 {commit}</code></p><ul>{file_rows}</ul>
<p><a href="/api/v4/projects/42/merge_requests/18">历史 MR !18：共享 SDK 与应用层的职责</a></p>
<h2>资料进入工作台的路径</h2><p>Harness → MCP 工具 → 本服务 HTTP API → 原始对象、版本与正文 → 下一轮模型输入</p>
</html>'''

    def dispatch(self, path: str, query: dict[str, list[str]]) -> tuple[int, dict | str]:
        if path == "/":
            return 200, self.home()
        if path == "/health":
            return 200, {"status": "ok", "mode": "classroom-http-fixture"}
        if path == "/rest/api/3/issue/KNOW-201":
            return 200, self.issue()
        if path == "/wiki/rest/api/content/search":
            cql = query.get("cql", [""])[0]
            label = re.search(r'label\s*=\s*"project-([a-z0-9_-]+)"', cql)
            text = re.search(r'text\s*~\s*"((?:\\.|[^"\\])*)"', cql)
            if not label:
                return 400, {"error": "本课堂搜索要求明确 project 标签"}
            word = text.group(1).replace('\\"', '"').replace('\\\\', '\\') if text else ""
            docs = [d for d in self.documents() if d["project_key"] == label.group(1)
                    and word.casefold() in (d["title"] + d["body"]).casefold()]
            results = [{"id": str(d["page_id"]), "title": d["title"], "type": "page",
                        "version": {"number": d["version"]}, "metadata": {"labels": {"results": [{"name": "project-" + d["project_key"]}]}},
                        "_links": {"webui": "/wiki/spaces/KNOW/pages/" + str(d["page_id"])}} for d in docs]
            return 200, {"results": results, "start": 0, "limit": 25, "size": len(results), "_links": {}}
        if match := re.fullmatch(r"/wiki/api/v2/pages/(\d+)", path):
            found = next((d for d in self.documents() if str(d["page_id"]) == match.group(1)), None)
            if not found or (query.get("version") and int(query["version"][0]) != found["version"]):
                return 404, {"error": "未找到该页面或版本"}
            return 200, self.page(found)
        if match := re.fullmatch(r"/api/v4/projects/42/repository/files/(.+)", path):
            try:
                return 200, self.repository_file(unquote(match.group(1)), query.get("ref", ["HEAD"])[0])
            except (subprocess.CalledProcessError, ValueError):
                return 404, {"error": "该提交下没有这份文件"}
        if path == "/api/v4/projects/42/merge_requests/18":
            return 200, {"id": 18, "iid": 18, "project_id": 42, "state": "merged",
                         "title": "共享 Wiki SDK 保持稳定，业务范围由应用层组织",
                         "description": "SDK 已供知识门户与资料校验两个应用使用。项目过滤和变更订阅由应用层组合；本次 KNOW-201 不修改 shared/wiki_sdk.py。页面迁移时同时保留变更前后的项目归属，订阅方需要据此判断影响。",
                         "sha": self.git("rev-parse", "HEAD"), "web_url": "/gitlab/42/-/merge_requests/18"}
        return 404, {"error": "课程隔离服务没有这个对象", "path": path}


def create_server(host: str, port: int, fixture: EnterpriseFixture) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parts = urlsplit(self.path)
            try:
                status, data = fixture.dispatch(parts.path, parse_qs(parts.query))
            except (ValueError, KeyError, FileNotFoundError) as error:
                status, data = 400, {"error": str(error)}
            raw = data.encode() if isinstance(data, str) else json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8" if isinstance(data, str) else "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            fixture.record({"time": datetime.now(timezone.utc).isoformat(), "method": "GET", "path": self.path,
                            "status": status, "response_sha256": hashlib.sha256(raw).hexdigest(), "response_bytes": len(raw)})

        def log_message(self, *_):
            pass
    return ThreadingHTTPServer((host, port), Handler)


def prepare_repository(repo_root: Path) -> Path:
    """为 GitHub 源码包建立隔离的 Git 快照，供演示 GitLab API 读取。"""
    if (repo_root / '.git').exists():
        return repo_root
    repo = LAB / 'runs/service-repository'
    if not (repo / '.git').exists():
        shutil.copytree(repo_root, repo, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        subprocess.run(['git','init','-b','main',str(repo)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(repo),'add','.'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(repo),'-c','user.name=Workshop',
                        '-c','user.email=workshop@example.invalid','commit','-m','initial project snapshot'],
                       check=True,capture_output=True)
    return repo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--repo-root", type=Path, default=LAB / "starter")
    parser.add_argument("--log", type=Path, default=LAB / "artifacts/http-requests.jsonl")
    args = parser.parse_args()
    if shutil.disk_usage(HERE).free < 384 * 1024**2:
        raise SystemExit("磁盘空间不足 384 MiB，停止启动。")
    repo = prepare_repository(args.repo_root)
    service = create_server("127.0.0.1", args.port, EnterpriseFixture(repo, args.log))
    print(f"课程隔离 HTTP 服务：http://127.0.0.1:{service.server_port}（Ctrl-C 停止）", flush=True)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.server_close()


if __name__ == "__main__":
    main()
