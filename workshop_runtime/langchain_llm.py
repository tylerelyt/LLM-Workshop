"""把课程 Chat Completions 客户端接入现有的 LangChain 文本工作流。"""
from typing import Optional
from langchain_core.language_models.llms import LLM
from .chat import chat


class WorkshopLLM(LLM):
    model: Optional[str] = None

    @property
    def _llm_type(self):
        return 'workshop-chat-completions'

    @property
    def _identifying_params(self):
        return {'model': self.model or 'configured-model'}

    def _call(self, prompt, stop=None, run_manager=None, **kwargs):
        text = chat(messages=[{'role': 'user', 'content': prompt}], model=self.model)
        # 老的文本 Agent 用 stop 分隔 Thought 与 Observation；截断不冒充工具执行。
        positions = [text.find(marker) for marker in (stop or []) if marker and marker in text]
        return text[:min(positions)] if positions else text
