
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workshop_runtime.chat import chat

def cross_session_reasoning(problem, questions):
    previous_answers = []
    for index, question in enumerate(questions, 1):
        history = "\n\n".join(previous_answers) or "None yet."
        prompt = (
            f"Problem: {problem}\n\nPrevious answers:\n{history}\n\n"
            f"This turn: {question}\nAnswer in at most three sentences."
        )
        response = chat(messages=[
            {'role': 'user', 'content': prompt},
        ])
        answer = response
        print(f"\nTurn {index}: {question}\n{answer}")
        previous_answers.append(f"Q: {question}\nA: {answer}")

    history = "\n\n".join(previous_answers)
    final_prompt = (
        f"Problem: {problem}\n\nPrior turns:\n{history}\n\n"
        "Give a final recommendation. Include the total cost and remaining budget."
    )
    final_response = chat(messages=[
        {'role': 'user', 'content': final_prompt},
    ])
    return final_response

problem = (
    "A workshop has a budget of $200 and 23 learners. Supplies are sold in $32 packs "
    "of five, and each learner needs one set. Reserve $35 for the room."
)
questions = [
    "How many whole packs are needed?",
    "Use the pack count from the previous turn to calculate the supply cost.",
    "Use that cost to decide whether we can afford supplies and the room."
]

result = cross_session_reasoning(problem, questions)
print(f'\nFinal answer:\n{result}')
