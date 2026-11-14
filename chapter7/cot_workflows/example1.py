
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workshop_runtime.chat import chat

def cot(problem):
    # 提示模型逐步思考
    prompt = f"{problem} Let's think step by step."
    response = chat(messages=[
        {
            'role': 'user',
            'content': prompt,
        },
    ])
    return response

def solve_math_problem():
    problem = "What is 5 + 3 + 7?"
    result = cot(problem)
    return result

result = solve_math_problem()
print(result)