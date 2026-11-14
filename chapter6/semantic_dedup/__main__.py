"""运行本课的独立实验，可选择在线模型。"""
import argparse
import json
from .lab import run
from ..shared.demo_output import show


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=str)
    parser.add_argument("--json", action="store_true", help="在终端显示完整 JSON，代替课堂摘要")
    args = parser.parse_args()
    ask = None
    if args.live:
        from workshop_runtime.deepseek import DeepSeek
        model = DeepSeek()
        def ask(system, user):
            return model.complete([{"role":"system","content":system},{"role":"user","content":user}], thinking=False, max_tokens=4096).content
    result = run(ask)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        from pathlib import Path
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered)
    if args.json:
        print(rendered, end="")
    else:
        show(5, result)
        if args.output:
            print(f"完整轨迹：{args.output}")
    if result.get("passed") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
