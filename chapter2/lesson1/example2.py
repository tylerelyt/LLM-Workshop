import ollama


def summarize_dialogue(dialogue_history):
    # 历史对话压缩，提取关键信息
    relevant_dialogue = "\n".join(line for line in dialogue_history.split("\n") if "用户:" in line or "客服:" in line)

    # 生成对话摘要的提示词，强调保留数字和地点等关键信息
    prompt = (
        f"请提取以下对话的关键信息，并生成摘要，保留数字和地点等重要信息，去除不必要的细节:\n\n{relevant_dialogue}"
    )

    # 使用 Ollama 进行对话摘要生成，并指定用中文回答
    messages = [
        {'role': 'user', 'content': prompt},
        {'role': 'system', 'content': '请用中文回答'}
    ]

    response = ollama.chat(model='llama3', messages=messages)

    # 提取并清理模型的回复
    summary = response['message']['content'].strip()

    return summary


# 示例对话记录
dialogue_history = (
    "用户: 你好，你怎么样？\n"
    "客服: 我很好，谢谢！请问今天有什么可以帮助您的？\n"
    "用户: 我需要帮助处理我的账户。您能查看我的余额吗？\n"
    "客服: 当然可以！请提供您的账户号码。\n"
    "用户: 我的账户号码是123456。\n"
    "客服: 让我为您查一下...\n"
    "客服: 您的当前余额是$500。\n"
    "用户: 谢谢！您能告诉我最近的交易吗？\n"
    "客服: 我需要验证您的身份才能提供交易详细信息。\n"
    "用户: 好的，这里是我有的详细信息。\n"
)

# 生成摘要
summary = summarize_dialogue(dialogue_history)
print("对话摘要:\n", summary)

# 压缩历史对话信息
dialogue_history = summary