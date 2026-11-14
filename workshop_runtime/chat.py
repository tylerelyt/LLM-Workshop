"""课程文字生成入口。请求显式传入消息，不在模型客户端保存会话历史。"""
from .deepseek import DeepSeek


def chat(*, messages, model=None, max_tokens=4096):
    reply = DeepSeek(model=model).complete(messages, thinking=False, max_tokens=max_tokens)
    if not isinstance(reply.content, str) or not reply.content.strip():
        raise RuntimeError('模型没有返回可用正文。')
    return reply.content
