import ollama

def cot(problem):
    # 提示模型逐步思考
    prompt = f"{problem} Let's think step by step."
    response = ollama.chat(model='llama3', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
    ])
    return response['message']['content']

def solve_math_problem():
    problem = "What is 5 + 3 + 7?"
    result = cot(problem)
    return result

result = solve_math_problem()
print(result)