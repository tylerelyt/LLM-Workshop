"""多次采样、弃权与正确性分别评估；支持在线模型和明确标注的固定回复回放。"""
import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import DeepSeek

PROMPT = (
    "三个花坛分别需要10升、20升和30升水，总共需要多少升？"
    "可以简要解释。最后单独一行写‘最终答案：数值’，不要在这行之后增加其他数字。"
)


def extract_answer(text):
    last = text.strip().splitlines()[-1] if text.strip() else ''
    match = re.fullmatch(r'(?:最终答案|Final answer)\s*[:：]\s*([-+]?\d+(?:\.\d+)?)\s*(?:升|L)?[。.]?', last, re.IGNORECASE)
    return Decimal(match.group(1)) if match else None


def choose_answer(answers):
    counts = Counter(answer for answer in answers if answer is not None)
    if not counts:
        return None
    answer, votes = counts.most_common(1)[0]
    return answer if votes > len(answers) / 2 else None


def evaluate(question, expected, responses):
    parsed = [extract_answer(text) for text in responses]
    majority = choose_answer(parsed)
    return {'question': question, 'expected': str(expected),
            'samples': [{'response': text, 'parsed': str(value) if value is not None else None}
                        for text, value in zip(responses, parsed)],
            'valid_answers': sum(value is not None for value in parsed),
            'votes': {str(key): value for key, value in Counter(x for x in parsed if x is not None).items()},
            'majority': str(majority) if majority is not None else None,
            'single_correct': bool(parsed and parsed[0] == expected),
            'majority_correct': majority == expected, 'abstained': majority is None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials', type=int, choices=range(1, 22), default=3, metavar='1-21')
    parser.add_argument('--question', help='自拟题须同时指定独立计算的 --expected')
    parser.add_argument('--expected', type=str)
    parser.add_argument('--replay', type=Path, help='读取教学回复，明确显示为回放；不会调用模型')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.question is not None and not args.question.strip():
        parser.error("--question 不能为空。")
    responses, usages = [], []
    if args.replay:
        try:
            data = json.loads(args.replay.read_text(encoding='utf-8'))
            responses = data['responses']
            question = data['question']
            expected = Decimal(args.expected if args.expected is not None else str(data['expected']))
            if not isinstance(question, str) or not isinstance(responses, list) or not all(isinstance(x, str) for x in responses):
                raise ValueError('question 应为文字，responses 应为文字数组')
            if args.trials > len(responses):
                raise ValueError('回放回复不足，请减小 --trials')
            if args.question is not None and args.question != question:
                raise ValueError('不能把旧回复当成新题目的模型结果')
            responses = responses[:args.trials]
        except (OSError, ValueError, KeyError, TypeError, InvalidOperation) as error:
            parser.error(f'回放材料无效：{error}')
        mode, model = 'synthetic_replay', None
        print('模式：固定教学回复回放；没有在线模型调用。')
    else:
        if args.question is not None and args.expected is None:
            parser.error('自拟题需要 --expected，以独立答案核对投票结果。')
        question = args.question or PROMPT
        try:
            expected = Decimal(args.expected if args.expected is not None else '60')
        except InvalidOperation:
            parser.error('--expected 应是有限数值。')
        if not expected.is_finite():
            parser.error("--expected 应是有限数值。")
        backend = DeepSeek()
        mode, model = 'online_model', backend.model
        print(f'模式：在线模型 {model}')
    if not expected.is_finite():
        parser.error('--expected 应是有限数值。')
    started = perf_counter()
    if mode == 'online_model':
        for _ in range(args.trials):
            response = backend.complete([{'role': 'system', 'content': '根据给定条件提供一种解法。'},
                                         {'role': 'user', 'content': question}], thinking=False, max_tokens=256)
            if not isinstance(response.content, str) or not response.content.strip():
                raise RuntimeError('模型没有返回正文。')
            responses.append(response.content)
        usages = backend.usage
    result = evaluate(question, expected, responses)
    result.update({'mode': mode, 'model': model, 'model_calls': args.trials if model else 0,
                   'usage': usages, 'elapsed_seconds': perf_counter() - started})
    print('问题：' + question)
    for index, row in enumerate(result['samples'], 1):
        print(f"回复 {index}：{row['response']}\n解析：{row['parsed']}")
    print(f"有效答案：{result['valid_answers']}/{len(responses)}；票数：{result['votes']}")
    print(f"首轮正确：{result['single_correct']}；多数正确：{result['majority_correct']}；弃权：{result['abstained']}")
    print(f"独立答案：{expected}；多数结论：{result['majority']}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'完整结果：{args.output}')
    return 2 if result['abstained'] else (0 if result['majority_correct'] else 1)


if __name__ == '__main__':
    raise SystemExit(main())
