import torch
from modelscope import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

# 下载模型
cache_dir = './llama_cache'
model_id = snapshot_download("LLM-Research/Meta-Llama-3-8B", cache_dir=cache_dir)
