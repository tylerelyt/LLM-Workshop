import ollama

def decompose_task(task_description):
    # 假设这里有一个逻辑来分解任务
    return [
        {"role": "analyst", "description": "analyze the data"},
        {"role": "developer", "description": "write the code"},
        # 添加更多步骤...
    ]

def combine_results(results):
    # 假设这里有逻辑来组合结果
    return " ".join(results)

def task_decomposition(task_description):
    steps = decompose_task(task_description)
    results = []
    for step in steps:
        # 每个步骤都有明确的职责和约束
        prompt = f"As a {step['role']}, let's solve the specific part: {step['description']}"
        response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': prompt},
        ])
        results.append(response['message']['content'])

    # 综合所有步骤的结果，得出最终结论
    final_result = combine_results(results)
    return final_result

task_description = "Complex task involving multiple roles and responsibilities."
result = task_decomposition(task_description)
print(result)