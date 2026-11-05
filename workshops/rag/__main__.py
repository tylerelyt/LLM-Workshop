"""Run one RAG system through retrieval, maintenance, feedback, and Harness integration."""

import argparse
import json
import runpy
from importlib import import_module
from pathlib import Path

LABS = ("reranker", "dedup", "quality", "language", "graph", "mcp")


def run(labs, live=False):
    client = None
    if live and any(name != "reranker" for name in labs):
        from workshop_runtime.deepseek import DeepSeek

        client = DeepSeek(model="deepseek-flash")

    def ask(system: str, user: str) -> str:
        message = client.complete(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            thinking=False,
            max_tokens=4096,
        )
        if not message.content:
            raise RuntimeError("DashScope returned no response text.")
        return message.content

    results = {}
    for name in labs:
        if name == "reranker":
            directory = Path(__file__).resolve().parent / "reranker"
            if live:
                result = runpy.run_path(str(directory / "lab.py"))["RESULT"]
            else:
                result = json.loads((directory / "replay.json").read_text())
                result["mode"] = "recorded_replay"
            calls = result.get("usage", [])
            results[name] = {
                "api_calls": len(calls),
                "prompt_tokens": sum(call.get("prompt_tokens") or 0 for call in calls),
                "completion_tokens": sum(call.get("completion_tokens") or 0 for call in calls),
                "result": result,
            }
            continue
        module = ".mcp_harness.__main__" if name in ("mcp", "mcp_harness") else f".{name}.lab"
        lab = import_module(module, __package__)
        start = len(client.usage) if client else 0
        if name in ("mcp", "mcp_harness"):
            result = lab.run_workshop(live=live, model=client)
        else:
            result = lab.run(ask if client else None)
        calls = client.usage[start:] if client else []
        results[name] = {
            "api_calls": len(calls),
            "prompt_tokens": sum(call.get("prompt_tokens") or 0 for call in calls),
            "completion_tokens": sum(call.get("completion_tokens") or 0 for call in calls),
            "result": result,
        }
    return {"provider": ("mixed" if client and "reranker" in labs else "deepseek" if client else "dashscope") if live else None, "mode": "live" if live else "offline",
            "model": client.model if client else (results.get("reranker", {}).get("result", {}).get("model") if live else None), "labs": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", choices=("all", *LABS, "mcp_harness"))
    parser.add_argument("--live", action="store_true", help="Run live APIs (DashScope for the first RAG exercise)")
    parser.add_argument("--output", type=Path, help="Write the complete JSON record to this file")
    args = parser.parse_args()
    payload = run(LABS if args.lab == "all" else (args.lab,), args.live)
    passed = all(entry["result"].get("passed", True) for entry in payload["labs"].values())
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Written to {args.output}")
    else:
        print(rendered, end="")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
