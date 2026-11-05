import ollama

def cross_session_reasoning(session_data):
    accumulated_info = ""
    for session in session_data:
        print(session)
        prompt = f"Based on our previous discussions: {accumulated_info} {session['question']}"
        response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': prompt},
        ])
        print(response['message']['content'])
        accumulated_info += response['message']['content'] + " "

    final_prompt = f"Now, let's summarize the conclusion based on all the steps we've discussed: {accumulated_info.strip()}"
    print(final_prompt)
    final_response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': final_prompt},
    ])
    return final_response['message']['content']

session_data = [
    {"question": "What foundational concepts should we consider when addressing problem X?"},
    {"question": "Based on those concepts, what is the initial action we should take to approach problem X?"},
    {"question": "What factors should we evaluate after the initial action to determine its effectiveness?"},
    {"question": "Considering the evaluation results, what would be the next logical step?"},
    {"question": "What potential challenges might arise from this next step, and how can we mitigate them?"},
    {"question": "Finally, how can we integrate all these steps to formulate a comprehensive solution to problem X?"}
]

result = cross_session_reasoning(session_data)
print(f'\nFinal answer:\n{result}')
