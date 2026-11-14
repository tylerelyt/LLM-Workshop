import argparse
import os
from local_model import load_local_model

model_path = './llama_cache/LLM-Research/Meta-Llama-3-8B-Instruct'

# Google Custom Search API配置
API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# 检索相关文档的函数
def retrieve_documents(query):
    if not (API_KEY and SEARCH_ENGINE_ID):
        print("Using a local teaching passage. Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID for live search.")
        return ["Paris is the capital and most populous city of France."]

    from googleapiclient.discovery import build

    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()
        results = res.get('items', [])
        documents = [item["snippet"] for item in results]
        return documents
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []


def deepseek_search(query):
    import requests

    key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
    if not key and base_url in ("https://api.deepseek.com", "https://api.deepseek.com/v1"):
        key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit(
            "Set DEEPSEEK_API_KEY, or set OPENAI_API_KEY with OPENAI_BASE_URL=https://api.deepseek.com."
        )

    try:
        response = requests.post(
            "https://api.deepseek.com/v1/tools/search",
            headers={"Authorization": f"Bearer {key}"},
            json={"query": f"{query} site:france.fr lang:en", "count": 3},
            timeout=30,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise SystemExit("Could not reach DeepSeek Search. Check the network and try again.") from None
    if response.status_code != 200:
        raise SystemExit(f"DeepSeek Search returned HTTP {response.status_code}. Check the API key and account access.")

    documents = []
    for result in response.json()["results"]:
        snippet = (result.get("snippet") or "").strip()[:400]
        if snippet:
            print(f"Source {len(documents) + 1}: {result['title']}\n{result['url']}\n{snippet}", flush=True)
            documents.append(snippet)
    if not documents:
        raise SystemExit("DeepSeek Search returned no usable excerpts.")
    return documents


# 生成答案的函数
def generate_answer(query, documents):
    tokenizer, model = load_local_model(model_path)
    excerpts = "\n\n".join(documents[:3])
    prompt = (
        "Answer the question in one sentence using only the supplied excerpts. "
        "If the answer is not in the excerpts, say so.\n\n"
        f"Excerpts:\n{excerpts}\n\nQuestion: {query}"
    )
    if tokenizer.chat_template:
        context = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
        )
    else:
        context = prompt + "\nAnswer:"
    inputs = tokenizer(
        context, return_tensors="pt", truncation=True, max_length=2048,
        add_special_tokens=not tokenizer.chat_template,
    ).to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=48)
    return tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

# 主函数
def main():
    parser = argparse.ArgumentParser(description="Answer a question with a local model and retrieved passages.")
    parser.add_argument("--deepseek-search", action="store_true", help="Search France.fr with the DeepSeek API")
    args = parser.parse_args()
    query = "What is the capital of France?"
    documents = deepseek_search(query) if args.deepseek_search else retrieve_documents(query)
    if documents:
        answer = generate_answer(query, documents)
        print("Question:", query)
        print("Answer:", answer)
    else:
        print("No documents retrieved.")

if __name__ == "__main__":
    main()
