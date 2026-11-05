import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

# 初始化对话历史
dialogue_history = [
    "Customer: Hi, I have an issue with my order.",
    "Support: Sure, could you please provide your order number?",
    "Customer: Sure, it's #12345.",
    "Support: Thank you. Let me check the status for you.",
]

# 合并对话历史为一个字符串
dialogue_history_text = "\n".join(dialogue_history)

# 添加用户输入，模拟当前对话
user_input = "Customer: Can you please expedite the delivery?"
input_text = dialogue_history_text + "\n" + user_input

# 生成文本
input_ids = tokenizer.encode(input_text, return_tensors="pt")
outputs = model.generate(input_ids, max_length=100)
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("Generated Response:", generated_text)

