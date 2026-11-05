import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# 加载分词器和模型
cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

# 编码输入并将其移至模型设备
input_text = "在一个阳光明媚的早晨，Alice决定去森林里探险。她走着走着，突然发现了一条小路。"
inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

# 生成并解码文本
with torch.no_grad():
    outputs = model.generate(**inputs)
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(generated_text)
