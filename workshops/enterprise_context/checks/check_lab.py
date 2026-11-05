"""按公开行为检查实现；不要求采用讲师参考的内部函数或调用顺序。"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

LAB = Path(__file__).resolve().parents[1]
BASE = LAB / "starter"


def load_application(path: Path):
    root = path.parent.parent
    sys.path.insert(0, str(root))
    for name in list(sys.modules):
        if name == "shared" or name.startswith("shared."):
            sys.modules.pop(name)
    spec = importlib.util.spec_from_file_location("checked_application", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def append_change(path: Path, page_id: str, version: int, event_id: str, project: str | None = None):
    data = json.loads(path.read_text())
    document = next(item for item in data["documents"] if str(item["page_id"]) == page_id)
    old_project = document["project_key"]
    document["version"] = version
    if project is not None:
        document["project_key"] = project
    data["events"].append({
        "seq": len(data["events"]) + 1,
        "event_id": event_id,
        "page_id": page_id,
        "old_project_key": old_project,
        "project_key": document["project_key"],
        "version": version,
    })
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def check(app_path: Path, sdk_path: Path) -> dict:
    module = load_application(app_path)
    baseline = json.loads((LAB / "checks/baseline.json").read_text())
    checks = []

    def record(name: str, passed: bool, actual):
        checks.append({"name": name, "passed": bool(passed), "actual": actual})

    with tempfile.TemporaryDirectory(prefix="project-knowledge-") as temp:
        data_path = Path(temp) / "wiki.json"
        data_path.write_bytes((BASE / "data/wiki.json").read_bytes())
        app = module.KnowledgeApplication(module.WikiSDK(data_path))
        global_result = app.search("")
        compatible = all(app.search(query) == expected for query, expected in baseline["global_search"].items())
        record("旧全局检索结果保持兼容", compatible,
               [item["page_id"] for item in global_result["items"]])
        sdk_unchanged = hashlib.sha256(sdk_path.read_bytes()).hexdigest() == baseline["sdk_sha256"]
        record("共享 SDK 内容保持不变", sdk_unchanged, str(sdk_path))
        try:
            project_result = app.search("", project_key="atlas")
            page_ids = {str(item["page_id"]) for item in project_result["items"]}
            record("按项目检索隔离同名文档", page_ids == {"100", "101", "102"}, sorted(page_ids))
            state = app.subscribe("atlas")
            append_change(data_path, "200", 7, "borealis-update")
            append_change(data_path, "100", 8, "atlas-design-update")
            append_change(data_path, "100", 8, "atlas-design-update")
            result = app.poll(state)
            notices = result["notifications"]
            observed = [(str(item["page_id"]), item["version"], item["action"]) for item in notices]
            record("只通知本项目新版本，重复事件不重复通知", observed == [("100", 8, "review")], observed)
            persisted = json.loads(json.dumps(result["state"]))
            restarted = module.KnowledgeApplication(module.WikiSDK(data_path))
            result = restarted.poll(persisted)
            record("状态保存后，换实例继续不会重发已处理通知", result["notifications"] == [], result["notifications"])
            append_change(data_path, "100", 9, "atlas-page-moved", "borealis")
            result = restarted.poll(result["state"])
            observed = [(str(item["page_id"]), item["version"], item["action"]) for item in result["notifications"]]
            record("文档迁出后原项目能移除旧依据", observed == [("100", 9, "remove")], observed)
            left_ids = {str(item["page_id"]) for item in restarted.search("", project_key="atlas")["items"]}
            record("后续项目检索与最新归属一致", left_ids == {"101", "102"}, sorted(left_ids))
            append_change(data_path, "100", 9, "atlas-page-returned", "atlas")
            result = restarted.poll(result["state"])
            observed = [(str(item["page_id"]), item["version"], item["action"]) for item in result["notifications"]]
            record("正文版本不变，迁回项目仍重新纳入依据", observed == [("100", 9, "review")], observed)
            append_change(data_path, "100", 9, "atlas-page-moved-without-body-change", "borealis")
            result = restarted.poll(result["state"])
            observed = [(str(item["page_id"]), item["version"], item["action"]) for item in result["notifications"]]
            record("正文版本不变，迁出项目仍撤出旧依据", observed == [("100", 9, "remove")], observed)
        except (AttributeError, TypeError) as error:
            record("新增项目检索与订阅接口已经实现", False, f"{type(error).__name__}: {error}")
    return {"passed": all(row["passed"] for row in checks), "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="核对项目知识平台的公开行为")
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--sdk", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    args.app = args.app.resolve()
    sdk = args.sdk or args.app.parent.parent / "shared/wiki_sdk.py"
    report = check(args.app, sdk)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    for item in report["checks"]:
        print(f"{'通过' if item['passed'] else '未完成'} | {item['name']} | {item['actual']}")
    raise SystemExit(0 if report["passed"] else 1)
