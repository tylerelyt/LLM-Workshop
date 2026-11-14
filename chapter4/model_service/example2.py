from local_model import load_local_model

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
tokenizer, model = load_local_model(model_path)

instruction = "请写一首关于爱情的中文短诗。"
messages = [{"role": "user", "content": instruction}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print(f"角色消息：{messages}")
print(f"Chat 模板转换后的文本：\n{prompt}")
inputs = tokenizer(prompt, add_special_tokens=False, return_tensors="pt").to(model.device)
print(f"输入 Token 数：{inputs.input_ids.shape[-1]}")
output = model.generate(**inputs, max_new_tokens=96)
answer = tokenizer.decode(output[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
print(f"指令：{instruction}\n回答：\n{answer.strip()}")
