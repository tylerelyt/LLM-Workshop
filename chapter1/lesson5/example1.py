import ollama

# 定义少样本提示词
few_shot_prompt = (
    "以下是关于电影评论的示例：\n"
    "输入：这部电影真是太棒了！\n"
    "输出：积极\n"
    "输入：我觉得这部电影很无聊。\n"
    "输出：消极\n"
    "请根据下面的评论判断其情感倾向：\n"
    "输入：我对这部电影感到失望。"
)

# 使用 Ollama 模型 'llama3' 进行对话
response = ollama.chat(model='llama3:text', messages=[
    {
        'role': 'user',
        'content': few_shot_prompt,
    },
])

# 输出模型生成的响应
print("模型生成的响应：\n", response['message']['content'])