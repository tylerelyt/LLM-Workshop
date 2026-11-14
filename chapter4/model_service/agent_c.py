# agent_c.py
from flask import Flask, request, jsonify
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import load_environment, uses_openai_config

from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
import requests

app = Flask(__name__)


def call_expert(url, task_requirement):
    response = requests.post(url, json={"intent": task_requirement}, timeout=45)
    response.raise_for_status()
    return response.json().get("response", "Error: No response from expert")

def ai_expert(task):
    return call_expert(f"http://127.0.0.1:{os.getenv('WORKSHOP_AI_PORT', '5000')}/chat", task)


def law_expert(task):
    return call_expert(f"http://127.0.0.1:{os.getenv('WORKSHOP_LAW_PORT', '5001')}/chat", task)

ai = Tool.from_function(func=ai_expert, name="ai_expert", description="当你需要人工智能专家知识时使用这个工具，输入为具体问题，返回为问题答案")
law = Tool.from_function(func=law_expert, name="law_expert", description="当你需要法律合规专家知识时使用这个工具，输入为具体问题，返回为问题答案")

tools = [ai, law]

load_environment()
if uses_openai_config() or os.getenv("DEEPSEEK_API_KEY"):
    from workshop_runtime.langchain_llm import WorkshopLLM
    llm = WorkshopLLM()
elif os.getenv("OLLAMA_HOST"):
    from langchain_ollama import OllamaLLM

    llm = OllamaLLM(model=os.getenv("WORKSHOP_OLLAMA_MODEL", "llama3"))
else:
    from langchain_community.llms import HuggingFacePipeline
    from transformers import pipeline

    from local_model import load_local_model

    model_path = "./llama_cache/LLM-Research/Meta-Llama-3-8B-Instruct"
    tokenizer, model = load_local_model(model_path)
    pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer,
                    max_new_tokens=512, return_full_text=False, device=model.device)
    llm = HuggingFacePipeline(pipeline=pipe)

agent = initialize_agent(tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations = 5,
        handle_parsing_errors = True)

@app.route('/integrate', methods=['POST'])
def integrate():
    data = request.get_json()
    task = data.get('task', '')
    res = agent.invoke({'input': task})['output']
    return jsonify({'response': res})

if __name__ == '__main__':
    app.run(port=int(os.getenv('WORKSHOP_COORDINATOR_PORT', '5002')))
