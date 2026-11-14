
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workshop_runtime.chat import chat

def decompose_task():
    return [
        {"role": "analyst", "description": "Calculate the example average and explain the alert rule."},
        {"role": "developer", "description": "Write a Python function and two assertions, one for the example and one for equality."},
    ]

def task_decomposition(task_description):
    steps = decompose_task()
    results = []
    for step in steps:
        handoff = "\n\n".join(results) or "None yet."
        prompt = (
            f"Task: {task_description}\n\n"
            f"Earlier work:\n{handoff}\n\n"
            f"You are the {step['role']}. {step['description']}"
        )
        response = chat(messages=[
            {'role': 'user', 'content': prompt},
        ])
        results.append(f"[{step['role']}]\n{response}")
    return "\n\n".join(results)

task_description = (
    "Send a temperature alert when the arithmetic mean of a nonempty list of readings "
    "is at least the threshold. The example readings are 18, 21, and 24, and the threshold is 20."
)
result = task_decomposition(task_description)
print(result)
