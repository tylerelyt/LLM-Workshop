"""DeepSeek 官方接口；各练习共用配置，工具回合保留完整 assistant 消息。"""
from __future__ import annotations
import os
from pathlib import Path

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
        if separator and name.startswith(('DEEPSEEK_', 'HF_', 'FASTEMBED_')):
            os.environ.setdefault(name, value.strip().strip('\"').strip("'"))


def model_name(model: str | None = None) -> str:
    load_environment()
    return model or os.environ.get('DEEPSEEK_MODEL', 'deepseek-flash')


class DeepSeek:
    def __init__(self, model: str | None = None, api_key: str | None = None):
        load_environment()
        from openai import OpenAI
        key = api_key or os.environ.get('DEEPSEEK_API_KEY')
        if not key:
            raise ValueError('请设置 DEEPSEEK_API_KEY，或用 DEEPSEEK_ENV_FILE 指定本机环境文件。')
        self.model = model_name(model)
        self.client = OpenAI(api_key=key,
            base_url=os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
            timeout=90.0, max_retries=1)
        self.usage: list[dict] = []

    def complete(self, messages: list, *, tools: list | None = None,
                 thinking: bool = True, max_tokens: int = 4096, json_output: bool = False):
        options = dict(model=self.model, messages=messages, max_tokens=max_tokens,
            extra_body={'thinking': {'type': 'enabled' if thinking else 'disabled'}})
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
