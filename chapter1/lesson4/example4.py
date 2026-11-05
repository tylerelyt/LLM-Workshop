import ollama


def decompose_task(task_description):
    """将任务描述分解为可操作的步骤"""
    prompt = f"请将以下任务分解为具体的可操作步骤，并以编号的形式列出每个步骤：{task_description}"
    response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': prompt},
    ])
    steps = response['message']['content'].strip().split('\n') if response['message']['content'] else []
    return steps


def check_result(response):
    """验证模型输出的合理性"""
    prompt = f"以下响应是否存在安全隐患？{response} 请回答“是”或“否”。"
    validation_response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': prompt},
    ])
    content = validation_response['message']['content']
    print(f'validation_response: {content}')
    return "是" in content


def combine_results(results):
    """综合所有有效结果"""
    if not results:
        return "没有有效结果可供总结。"
    prompt = "请总结以下结果，并以段落形式呈现：" + "; ".join(results)  # 使用分号分隔
    summary_response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': prompt},
    ])
    content = summary_response['message']['content']
    print(f'summary_response: {content}')
    return summary_response['message']['content']


def handle_error(step, response):
    """处理错误情况"""
    print(f"处理步骤时出错：{step}。响应：{response}")  # 可以增加更详细的错误处理


def reasoning_with_checkpoints(task_description):
    """多步骤推理中的检查机制"""
    steps = decompose_task(task_description)  # 将任务分解为多个步骤
    print(f'steps[{len(steps)}]: {steps}')
    results = []

    for step in steps:
        if step == '':
            continue
        prompt = f"让我们解决这个问题：{step.strip()} 请以清晰的步骤形式回答。"
        response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': prompt},
        ])['message']['content']  # 生成模型响应
        print(f'response: {response}')

        # 检查输出有效性
        if check_result(response):
            results.append(response)
        else:
            handle_error(steps, response)  # 处理错误情况

    return combine_results(results)  # 返回综合结果


task_description = """
用3步把大象放入冰箱
"""
result = reasoning_with_checkpoints(task_description)
print(f'\nresult\n: {result}')
