"""Load the local model used by the foundation examples."""

import os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_local_model(default_path):
    model_path = os.getenv("WORKSHOP_LOCAL_MODEL", default_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=dtype)
    if torch.cuda.is_available():
        model = model.to("cuda")
    return tokenizer, model
