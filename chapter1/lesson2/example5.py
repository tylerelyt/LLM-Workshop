import ollama

# 读取法律文书内容
with open('data/legal_document.txt', 'r', encoding='utf-8') as f:
    legal_text = f.read()

# 系统提示词
SYSTEM_PROMPT = (
    f'法律文书内容: {legal_text}\n\n'
    '上下文: 你是一个法律助手，基于提供的法律文书内容提供答案。'
    '你只能讨论文书中的内容。用户将询问有关文书的具体问题，'
    '你需要基于文书内容提供详细的回答。如果信息不足以回答问题，'
    '请要求用户提供更具体的文书部分。'
)

# 用户问题
QUESTION = '文中关于合同中的主要义务的描述是否一致？'

# 构造聊天消息
messages = [
    {'role': 'system', 'content': SYSTEM_PROMPT},
    {'role': 'user', 'content': QUESTION},
]

# 调用Ollama的LLM生成结果
response = ollama.chat(model='llama3-gradient', messages=messages)

# 输出结果
print('\n\n')
print(f'系统提示: ...{SYSTEM_PROMPT[-500:]}')  # 打印最后500个字符的系统提示
print(f'用户提问: {QUESTION}')
print('回答:')
print(response['message']['content'])  # 输出生成的回答
