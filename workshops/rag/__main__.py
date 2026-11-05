"""运行逐步完善同一套 RAG：检索、维护、反馈与 Harness 接入。"""

import argparse
import json
from importlib import import_module
from pathlib import Path

LABS = ("reranker", "dedup", "quality", "language", "graph", "mcp")


def run(labs, live=False):
    client = None
    if live:
        from workshop_runtime.deepseek import DeepSeek

        client = DeepSeek(model="deepseek-flash")

    def ask(system: str, user: str) -> str:
        message = client.complete(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            thinking=False,
            max_tokens=4096,
        )
        if not message.content:
            raise RuntimeError("DeepSeek Flash 未返回正文。")
        return message.content

    results = {}
    for name in labs:
        module = ".mcp_harness.__main__" if name in ("mcp", "mcp_harness") else f".{name}.lab"
        lab = import_module(module, __package__)
        start = len(client.usage) if client else 0
        if name in ("mcp", "mcp_harness"):
            result = lab.run_workshop(live=live, model=client)
        elif name == "reranker":
            result = lab.run(client)
        else:
            result = lab.run(ask if client else None)
        calls = client.usage[start:] if client else []
        results[name] = {
            "api_calls": len(calls),
            "prompt_tokens": sum(call.get("prompt_tokens") or 0 for call in calls),
            "completion_tokens": sum(call.get("completion_tokens") or 0 for call in calls),
            "result": result,
        }
    return {"mode": "live" if client else "offline", "model": client.model if client else None, "labs": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", choices=("all", *LABS, "mcp_harness"))
    parser.add_argument("--live", action="store_true", help="实际请求 DeepSeek Flash")
    parser.add_argument("--output", type=Path, help="将完整 JSON 记录写入指定文件")
    args = parser.parse_args()
    payload = run(LABS if args.lab == "all" else (args.lab,), args.live)
    passed = all(entry["result"].get("passed", True) for entry in payload["labs"].values())
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"已写入 {args.output}")
    else:
        print(rendered, end="")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
