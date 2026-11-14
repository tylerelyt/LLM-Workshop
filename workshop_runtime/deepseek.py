"""课程共用的 OpenAI Chat Completions 客户端，兼容已有 DeepSeek 配置。"""
from __future__ import annotations
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def load_environment() -> None:
    """读取指定的环境文件或仓库 .env，不覆盖已有环境变量。"""
    target = Path(os.environ.get('DEEPSEEK_ENV_FILE', ROOT / '.env')).expanduser()
    if not target.exists():
        return
    for raw in target.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        name, separator, value = line.partition('=')
        if separator and name.startswith(('OPENAI_', 'DEEPSEEK_', 'DASHSCOPE_', 'WORKSHOP_LOCAL_', 'HF_', 'FASTEMBED_')):
            os.environ.setdefault(name, value.strip().strip('\"').strip("'"))


def model_name(model: str | None = None) -> str:
    load_environment()
    if uses_openai_config():
        selected = model or os.environ.get('OPENAI_MODEL')
        if not selected:
            raise ValueError('请设置 OPENAI_MODEL 或通过 --model 指定服务商的模型名。')
        return selected
    return model or os.environ.get('DEEPSEEK_MODEL') or 'deepseek-flash'


def uses_openai_config() -> bool:
    return any(os.environ.get(name) for name in ('OPENAI_BASE_URL', 'OPENAI_API_KEY', 'OPENAI_MODEL'))


class DeepSeek:
    def __init__(self, model: str | None = None, api_key: str | None = None):
        load_environment()
        from openai import OpenAI
        compatible = uses_openai_config()
        self.provider = 'openai-compatible' if compatible else 'deepseek'
        key_var = 'OPENAI_API_KEY' if compatible else 'DEEPSEEK_API_KEY'
        key = api_key or os.environ.get(key_var)
        if not key:
            raise ValueError(f'请设置 {key_var}，或用 DEEPSEEK_ENV_FILE 指定本机环境文件。')
        self.model = model_name(model)
        if compatible:
            base_url = os.environ.get('OPENAI_BASE_URL') or 'https://api.openai.com/v1'
        else:
            base_url = os.environ.get('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com'
        hostname = urlsplit(base_url).hostname
        self.supports_deepseek_thinking = not compatible or hostname == 'api.deepseek.com'
        self.token_limit_field = 'max_completion_tokens' if hostname == 'api.openai.com' else 'max_tokens'
        self.client = OpenAI(api_key=key,
            base_url=base_url,
            timeout=90.0, max_retries=1)
        self.usage: list[dict] = []

    def complete(self, messages: list, *, tools: list | None = None,
                 thinking: bool = True, max_tokens: int = 4096, json_output: bool = False):
        options = dict(model=self.model, messages=messages)
        options[self.token_limit_field] = max_tokens
        if self.supports_deepseek_thinking:
            options['extra_body'] = {'thinking': {'type': 'enabled' if thinking else 'disabled'}}
            if thinking:
                options['reasoning_effort'] = 'low'
        if tools:
            options['tools'] = tools
        if json_output:
            options['response_format'] = {'type': 'json_object'}
        response = self.client.chat.completions.create(**options)
        if response.usage:
            self.usage.append(response.usage.model_dump())
        if response.choices[0].finish_reason == 'length':
            raise RuntimeError('模型输出达到上限；本轮没有完整结果，请提高 max_tokens 后重试。')
        return response.choices[0].message

    def json(self, messages: list, *, max_tokens: int = 4096) -> dict:
        import json
        message = self.complete(messages, thinking=False, max_tokens=max_tokens, json_output=True)
        if not message.content:
            raise RuntimeError('模型未返回 JSON 正文。')
        return json.loads(message.content)
