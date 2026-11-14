"""根据实际函数轨迹独立核对数列任务；两种循环实现共用相同的业务标准。"""
import json
import math
import random
import statistics


def verify_trace(trace, count, seed):
    if type(count) is not int or count <= 0:
        raise ValueError("count 必须是正整数。")
    rng = random.Random(seed)
    expected = [rng.randint(0, 100) for _ in range(count)]
    generated = None
    last_stats = None
    failures = []
    for index, call in enumerate(trace):
        result = call['result']
        if not isinstance(result, dict) or 'error' in result:
            failures.append(index)
            continue
        if call['function'] == 'generate_numbers':
            generated = result.get('numbers')
        elif call['function'] == 'calculate_stats':
            numbers = call['parameters'].get('numbers')
            if isinstance(numbers, str):
                try:
                    numbers = json.loads(numbers)
                except ValueError:
                    numbers = None
            last_stats = (numbers, result, generated)
    reference = {'count': count, 'sum': sum(expected), 'average': statistics.mean(expected),
                 'minimum': min(expected), 'maximum': max(expected), 'median': statistics.median(expected)}
    checks = {'generated_expected_data': isinstance(generated, list) and all(type(x) is int for x in generated) and generated == expected,
              'statistics_received_actual_data': bool(last_stats and last_stats[0] == last_stats[2] == expected),
              'statistics_match_independent_calculation': False}
    if last_stats:
        checks['statistics_match_independent_calculation'] = all(
            type(last_stats[1].get(key)) in (int, float)
            and math.isclose(last_stats[1][key], value, rel_tol=1e-10, abs_tol=1e-10)
            for key, value in reference.items())
    return {'passed': all(checks.values()), 'checks': checks, 'reference_statistics': reference,
            'reference_qualified': 60 <= reference['average'] <= 80 and reference['minimum'] >= 30,
            'tool_calls': len(trace), 'failed_tool_calls': failures,
            'final_answer_review': '对照 reference_qualified 人工核对模型结论；轨迹通过不等于结论正确'}
