# common.py
from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def create_app(seed_memory):
    app = Flask(__name__)

    cache_dir = './llama_cache'
    model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        pad_token_id=tokenizer.eos_token_id
    )

    # 定义聊天接口
    @app.route('/chat', methods=['POST'])
    def chat():
        data = request.get_json()
        intent = data.get('intent', '')

        # 构造提示词
        prompt = f"{seed_memory}\n请回答以下问题:{intent}"
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        outputs = model.generate(input_ids, max_length=150)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return jsonify({'response': response})

    return app
