
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse

from workshop_runtime.chat import chat


EXAMPLES = (
    "输入：这部电影真是太棒了！\n输出：积极\n"
    "输入：我觉得这部电影很无聊。\n输出：消极\n"
)
REVIEW = "我对这部电影感到失望。"


def build_prompt(with_examples=True):
    examples = EXAMPLES if with_examples else ""
    return (
        "判断电影评论的情感，只回答‘积极’或‘消极’。\n"
        + examples
        + f"输入：{REVIEW}\n输出："
    )


def main():
    parser = argparse.ArgumentParser(description="固定评论和模型，对照零样本与少样本提示。")
    parser.add_argument("--zero-shot", action="store_true", help="移除两个示例，其他条件不变")
    args = parser.parse_args()
    prompt = build_prompt(with_examples=not args.zero_shot)
    print(f"示例数：{0 if args.zero_shot else 2}\n实际提示：\n{prompt}")
    response = chat(messages=[{"role": "user", "content": prompt}])
    print("模型生成的响应：\n", response)


if __name__ == "__main__":
    main()
