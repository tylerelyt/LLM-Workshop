# agent_b.py
from common import create_app

app = create_app("system: 你是一个熟悉法律法规的法律专家。")

if __name__ == '__main__':
    app.run(port=5001)
