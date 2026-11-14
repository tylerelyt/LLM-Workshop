from local_model import load_local_model

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
tokenizer, model = load_local_model(model_path)

messages = [
    {"role": "system", "content": "You help customers check orders. Answer briefly using their previous messages."},
    {"role": "user", "content": "My order number is #12345."},
    {"role": "assistant", "content": "Thanks. How can I help?"},
    {"role": "user", "content": "What is my order number?"},
]

prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, add_special_tokens=False, return_tensors="pt").to(model.device)
output = model.generate(**inputs, max_new_tokens=48)
answer = tokenizer.decode(output[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
for message in messages[1:]:
    print(f"{message['role']}: {message['content']}")
print(f"assistant: {answer.strip()}")

