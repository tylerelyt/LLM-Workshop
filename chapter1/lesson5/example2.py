import ollama

# 定义零样本学习的提示词
zero_shot_prompt = "请用中文解释量子力学的基本概念。"

# 使用 Ollama 模型 'llama3' 进行对话
response = ollama.chat(model='llama3', messages=[
    {
        'role': 'user',
        'content': zero_shot_prompt,
    },
])

# 输出模型生成的响应
print("生成的输出：\n", response['message']['content'])