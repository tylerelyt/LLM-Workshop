import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

max_length = 50
input_text = "写一首关于爱情的诗"
encoded_input = tokenizer(input_text, return_tensors="pt")
output = model.generate(encoded_input.input_ids, max_length=max_length)
print(tokenizer.decode(output[0], skip_special_tokens=True))
