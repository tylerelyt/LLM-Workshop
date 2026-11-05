# agent_c.py
from flask import Flask, request, jsonify
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForCausalLM

from langchain.agents import initialize_agent, Tool, AgentType
from langchain.llms import HuggingFacePipeline
import requests
import torch

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

def call_expert(url, task_requirement):
    response = requests.post(url, json={"intent": task_requirement}, timeout=5)
    response.raise_for_status()
    return response.json().get("response", "Error: No response from expert")

ai_expert = lambda task: call_expert("http://localhost:5000/chat", task)
law_expert = lambda task: call_expert("http://localhost:5001/chat", task)

ai = Tool.from_function(func=ai_expert, name="ai_expert", description="当你需要人工智能专家知识时使用这个工具，输入为具体问题，返回为问题答案")
law = Tool.from_function(func=law_expert, name="law_expert", description="当你需要法律合规专家知识时使用这个工具，输入为具体问题，返回为问题答案")

tools = [ai, law]

pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)
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
    res = agent.run(task)
    return jsonify({'response': res})

if __name__ == '__main__':
    app.run(port=5002)
