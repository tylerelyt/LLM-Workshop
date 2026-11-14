"""运行计算器 Agent，观察模型动作与真实工具结果。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import json
import os
import math
from time import perf_counter
import numexpr as ne


def calculate_expression(expression):
    result = ne.evaluate(expression).item()
    print("TOOL_RESULT " + json.dumps({"expression": expression, "result": result}, ensure_ascii=False))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expression', default='37593 * 67')
    parser.add_argument('--model', default=None)
    parser.add_argument('--max-steps', type=int, default=5)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.max_steps < 1:
        parser.error('--max-steps 必须大于零。')
    try:
        expected = ne.evaluate(args.expression).item()
        if type(expected) not in (int, float) or not math.isfinite(expected):
            raise ValueError('需要有限的标量计算结果')
    except Exception as error:
        parser.error(f'表达式无效：{error}')
    from workshop_runtime.langchain_llm import WorkshopLLM
    from langchain.agents import initialize_agent
    from langchain.tools import Tool
    calls = []
    def execute(expression):
        result = calculate_expression(expression)
        calls.append({'expression': expression, 'result': result})
        return result
    tool = Tool(name='Numexpr Math', func=execute,
                description='计算数学表达式；参数为表达式字符串。')
    agent = initialize_agent(tools=[tool], llm=WorkshopLLM(model=args.model),
                             agent='zero-shot-react-description', verbose=True,
                             handle_parsing_errors=True, max_iterations=args.max_steps)
    question = f'使用 Numexpr Math 工具计算 {args.expression}，依据实际返回值回答。'
    print('用户问题：' + question)
    started = perf_counter()
    answer = agent.invoke({'input': question})['output']
    verified = any(type(call['result']) in (int, float) and math.isclose(call['result'], expected) for call in calls)
    stopped = answer.startswith('Agent stopped')
    report = {'expression': args.expression, 'reference': expected, 'trace': calls, 'answer': answer,
              'execution_verified': verified, 'budget_exhausted': stopped,
              'elapsed_seconds': perf_counter() - started,
              'answer_review': '将最终文字结论与真实工具返回分别核对'}
    print(answer)
    print(f'实际工具核对：{verified}；独立参考值：{expected}；预算耗尽：{stopped}')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if stopped or not verified:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
