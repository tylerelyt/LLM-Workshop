
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import json

from workshop_runtime.chat import chat


# 供窗口和摘要两个实验共用的固定教学对话。
HISTORY = [
    {"role": "user", "content": "我的账户号码是123456。"},
    {"role": "assistant", "content": "教学记录显示，您的余额是$500。"},
    {"role": "user", "content": "我想查看最近的交易。"},
    {"role": "assistant", "content": "查看交易明细之前需要验证身份。"},
    {"role": "user", "content": "我稍后再完成验证。"},
    {"role": "assistant", "content": "好的，完成验证后继续。"},
]
QUESTION = "刚才记录的账户号码和余额分别是多少？"


def customer_service_chat(history: list[dict], user_input: str, max_turns: int = 3):
    """按完整消息保留最近的对话轮次，返回更新后的应用历史与回复。"""
    if max_turns < 0:
        raise ValueError("max_turns 不能小于 0。")
    recent = history[-max_turns * 2:] if max_turns else []
    messages = [
        {"role": "system", "content": "只依据本次消息中的教学记录回答，缺少的信息明确说资料不足。"},
        *recent,
        {"role": "user", "content": user_input},
    ]
    print(f"本次发送的历史消息数：{len(recent)}")
    print("实际请求消息：" + json.dumps(messages, ensure_ascii=False))
    response = chat(messages=messages)
    reply = response.strip()
    return [*history, {"role": "user", "content": user_input},
            {"role": "assistant", "content": reply}], reply


def main():
    parser = argparse.ArgumentParser(description="固定问题，改变发送给模型的历史窗口。")
    parser.add_argument("--max-turns", type=int, choices=range(0, 21), default=3, metavar="0-20")
    args = parser.parse_args()
    _, reply = customer_service_chat(HISTORY, QUESTION, args.max_turns)
    print(f"问题：{QUESTION}\n回答：{reply}")


if __name__ == "__main__":
    main()
