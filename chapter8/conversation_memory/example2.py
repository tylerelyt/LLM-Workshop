
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workshop_runtime.chat import chat

if __package__:
    from .example1 import HISTORY, QUESTION, customer_service_chat
else:
    from example1 import HISTORY, QUESTION, customer_service_chat


def summarize_dialogue(dialogue_history):
    if isinstance(dialogue_history, list):
        text = "\n".join(f"{message['role']}: {message['content']}" for message in dialogue_history)
    else:
        text = dialogue_history
    prompt = (
        "请压缩以下教学对话，准确保留账户号码、余额及尚未完成的事项。"
        "只总结原文，不增加信息：\n\n" + text
    )
    response = chat(messages=[{"role": "user", "content": prompt}])
    summary = response.strip()
    if not summary:
        raise RuntimeError("摘要为空，不能继续问答。")
    return summary


def main():
    summary = summarize_dialogue(HISTORY)
    print("应用保存的摘要：\n" + summary)
    # 第二次请求只发送摘要，不发送生成摘要时的整段历史。
    compressed_history = [{"role": "assistant", "content": summary}]
    _, reply = customer_service_chat(compressed_history, QUESTION, max_turns=1)
    print(f"与窗口实验相同的问题：{QUESTION}\n回答：{reply}")


if __name__ == "__main__":
    main()
