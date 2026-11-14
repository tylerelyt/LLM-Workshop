import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import load_environment, uses_openai_config
from workshop_runtime.chat import chat as model_chat

from flask import Flask, request, jsonify

def create_app(seed_memory):
    app = Flask(__name__)

    load_environment()
    use_native = uses_openai_config() or bool(os.getenv("DEEPSEEK_API_KEY"))
    use_ollama = not use_native and bool(os.getenv("OLLAMA_HOST"))
    if use_ollama:
        import ollama
    elif not use_native:
        from local_model import load_local_model

        model_path = './llama_cache/LLM-Research/Meta-Llama-3-8B-Instruct'
        tokenizer, model = load_local_model(model_path)

    # 定义聊天接口
    @app.route('/chat', methods=['POST'])
    def chat():
        data = request.get_json()
        intent = data.get('intent', '')

        messages = [{"role": "system", "content": seed_memory},
                    {"role": "user", "content": intent}]
        if use_native:
            response = model_chat(messages=messages)
        elif use_ollama:
            reply = ollama.chat(model=os.getenv("WORKSHOP_OLLAMA_MODEL", "llama3"), messages=messages)
            response = reply.message.content
        else:
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt, add_special_tokens=False, return_tensors="pt").to(model.device)
            outputs = model.generate(**inputs, max_new_tokens=128)
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

        if not response or not response.strip():
            return jsonify({'error': '专家没有返回可用内容。'}), 502
        return jsonify({'response': response.strip()})

    return app
