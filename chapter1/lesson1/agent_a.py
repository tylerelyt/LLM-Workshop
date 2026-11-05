# agent_a.py
from common import create_app

app = create_app("system: 你是一个熟悉人工智能技术的计算机科学家。")

if __name__ == '__main__':
    app.run(port=5000)
