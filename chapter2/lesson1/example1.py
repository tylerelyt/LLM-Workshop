import ollama


def customer_service_chat(history: str, user_input: str, max_turns: int = 3) -> tuple[str, str]:
    """
    与客服进行对话，并维护对话历史。

    参数:
    history (str): 先前的对话历史。
    user_input (str): 用户当前的输入。
    max_turns (int): 需要保留的最大对话轮数。

    返回:
    tuple[str, str]: 更新后的对话历史和客服的回复。
    """
    # 分割历史对话成列表，保留最近 max_turns 轮对话
    history_lines = history.split("\n")
    recent_history = "\n".join(history_lines[-max_turns * 2:])  # 每轮对话包含用户和客服两句

    # 更新历史记录，拼接对话
    recent_history += f"\n用户: {user_input}\n客服:"

    # 使用 Ollama 进行对话，要求用中文回答，并明确指示上下文
    messages = [
        {'role': 'system', 'content': '请根据以下对话历史，用中文回答问题。'},
        {'role': 'user', 'content': recent_history}
    ]

    response = ollama.chat(model='llama3', messages=messages)

    # 提取并清理模型的回复
    reply = response['message']['content'].strip()

    # 更新历史，保留全量历史记录
    history += f"\n用户: {user_input}\n客服: {reply}"

    return history, reply


# 示例对话
history = "客服: 欢迎使用在线客服系统！请问有什么可以帮您？"
user_input = "我想预订一张飞往纽约的机票。"
history, reply = customer_service_chat(history, user_input)
print(f"用户: {user_input}\n客服: {reply}\n")

user_input = "有哪些航班可以选择？"
history, reply = customer_service_chat(history, user_input)
print(f"用户: {user_input}\n客服: {reply}")