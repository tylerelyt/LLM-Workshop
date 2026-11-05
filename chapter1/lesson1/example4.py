import requests
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from googleapiclient.discovery import build

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

# Google Custom Search API配置
API_KEY = 'YOUR_GOOGLE_API_KEY'
SEARCH_ENGINE_ID = 'YOUR_SEARCH_ENGINE_ID'

# 检索相关文档的函数
def retrieve_documents(query):
    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()
        results = res.get('items', [])
        documents = [item["snippet"] for item in results]
        return documents
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []

# 生成答案的函数
def generate_answer(query, documents):
    # 限制检索到的文档数量
    documents = documents[:3]
    context = "\n\n".join(documents) + "\n\nQuestion: " + query + "\nAnswer:"
    # 编码输入
    inputs = tokenizer(context, return_tensors="pt", truncation=True, max_length=2048).to(model.device)
    # 生成答案
    outputs = model.generate(**inputs, max_length=512)
    # 解码答案
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer

# 主函数
def main():
    query = "What is the capital of France?"
    documents = retrieve_documents(query)
    if documents:
        answer = generate_answer(query, documents)
        print("Question:", query)
        print("Answer:", answer)
    else:
        print("No documents retrieved.")

if __name__ == "__main__":
    main()
