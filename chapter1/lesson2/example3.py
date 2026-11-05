import chromadb
from chromadb.config import Settings
from FlagEmbedding import BGEM3FlagModel
import ollama  # 导入Ollama库

# 初始化Chroma数据库
chroma_client = chromadb.PersistentClient(path="./chromadb")

# 创建一些测试文档
documents = [
    {
        "page_content": "合同是两方或多方之间的法律协议，通常包括各方的权利和义务。合同必须具备合法性和可执行性。",
        "metadata": {"id": "doc1"}
    },
    {
        "page_content": "在合同中，主要义务包括：1) 付款义务，2) 商品交付义务，3) 相关服务的提供。合同中的这些义务必须在约定的时间内履行。",
        "metadata": {"id": "doc2"}
    },
    {
        "page_content": "合同的解除通常需要双方的同意，或者由于法律规定的特殊情况，如违约或不可抗力事件。",
        "metadata": {"id": "doc3"}
    },
    {
        "page_content": "违约责任是指一方未能履行合同义务时，应承担的法律后果，通常包括赔偿损失和继续履行合同的责任。",
        "metadata": {"id": "doc4"}
    },
    {
        "page_content": "在合同生效之前，所有相关方必须理解合同条款，并同意其内容。签字是合同生效的重要标志。",
        "metadata": {"id": "doc5"}
    },
    {
        "page_content": "合约的履行必须符合诚信原则，即各方应诚实守信地履行自己的义务，并尊重对方的合法权益。",
        "metadata": {"id": "doc6"}
    },
    {
        "page_content": "在合同争议中，双方可通过调解、仲裁或诉讼的方式解决争端。选择合适的方式取决于争议的性质及金额。",
        "metadata": {"id": "doc7"}
    },
    {
        "page_content": "关于合同的法律法规各国有所不同，了解适用的法律条款是签订合同前的重要步骤。",
        "metadata": {"id": "doc8"}
    }
]

# 初始化BGE M3模型
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

# 将文档添加到向量存储中
documentation_collection = chroma_client.get_or_create_collection(name="legal_docs")

# 生成文档嵌入并添加到集合中
for doc in documents:
    embedding = model.encode([doc['page_content']], batch_size=1)['dense_vecs'][0]
    documentation_collection.add(
        ids=[doc['metadata']['id']],  # 假设文档有唯一的id
        embeddings=[embedding],
        documents=[doc['page_content']]
    )

# 查询示例
query = "合同中的主要义务是什么？"
query_embedding = model.encode([query], batch_size=1)['dense_vecs'][0]

# 执行向量查询
results = documentation_collection.query(
    query_embeddings=[query_embedding],
    n_results=1  # 获取最相似的一个结果
)

# 提取检索到的文档内容
data = results['documents'][0]  # 假设只检索到一个结果
document_content = data  # 这里取出文档内容

# 将上下文与查询一起传递给 Ollama LLM
prompt = f"根据以下信息，请回答：{query}"

# 使用Ollama生成响应
output = ollama.chat(model='llama3', messages=[
    {
        'role': 'user',
        'content': f"使用以下数据：{document_content}. 响应这个提示：{prompt}"
    },
])

# 输出生成的结果
print("生成的结果：", output['message']['content'])
