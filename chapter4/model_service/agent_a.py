# agent_a.py
import os

from common import create_app

app = create_app("system: 你是一个熟悉人工智能技术的计算机科学家。")

if __name__ == '__main__':
    app.run(port=int(os.getenv("WORKSHOP_AI_PORT", "5000")))
