import argparse
import torch
from local_model import load_local_model

parser = argparse.ArgumentParser(description="观察续写输入、Token 与输出预算。")
parser.add_argument("--max-new-tokens", type=int, choices=range(1, 257), default=64, metavar="1-256")
args = parser.parse_args()

# 加载分词器和模型
cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B'
tokenizer, model = load_local_model(model_path)

# 编码输入并将其移至模型设备
input_text = "在一个阳光明媚的早晨，Alice决定去森林里探险。她走着走着，突然发现了一条小路。"
inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
print(f"输入 Token 数：{inputs.input_ids.shape[-1]}")
print(f"前 12 个 Token ID：{inputs.input_ids[0, :12].tolist()}")
print(f"前 12 个 Token 片段：{tokenizer.convert_ids_to_tokens(inputs.input_ids[0, :12].tolist())}")

# 生成并解码文本
with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=args.max_new_tokens, repetition_penalty=1.1)
continuation = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
print(f"开头：{input_text}\n续写：{continuation.strip()}")
generated = outputs.shape[-1] - inputs.input_ids.shape[-1]
print(f"输出 Token 数：{generated}；预算：{args.max_new_tokens}；是否达到预算：{generated == args.max_new_tokens}")
print(f"最后一个 Token ID：{outputs[0, -1].item()}；模型结束 Token ID：{model.generation_config.eos_token_id}")
