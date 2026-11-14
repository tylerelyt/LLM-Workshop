"""用同一 MaaS 配置对照独立请求与应用保存的 Session 历史。"""

import argparse
import json
from pathlib import Path
import sys
from copy import deepcopy
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import DeepSeek


SYSTEM = "只依据本次请求包含的消息回答。没有工单编号时回答‘资料不足’，不要猜测。简短作答。"


def ask(backend, session, message, records=None):
    session.append({"role": "user", "content": message})
    print("本次发送的消息：" + json.dumps(session, ensure_ascii=False), flush=True)
    usage_count = len(backend.usage)
    request = deepcopy(session)
    started = perf_counter()
    reply = backend.complete(session, thinking=False, max_tokens=256)
    elapsed = perf_counter() - started
    if not reply.content:
        raise RuntimeError("服务没有返回正文。")
    session.append({"role": "assistant", "content": reply.content})
    usage = backend.usage[-1] if len(backend.usage) > usage_count else {}
    print(f"回答：{reply.content}")
    print("服务报告的 Token 用量：" + (json.dumps(usage, ensure_ascii=False) if usage else "未报告"))
    if records is not None:
        records.append({'messages': request, 'answer': reply.content,
                        'elapsed_seconds': elapsed, 'usage': deepcopy(usage)})
    return reply.content


def run_experiment(backend, reference):
    records = []
    saved = [{'role': 'system', 'content': SYSTEM}]
    independent = [{'role': 'system', 'content': SYSTEM}]
    question = '本次工单编号是什么？'
    print('\nA：应用先记录一轮对话。')
    ask(backend, saved, f'本次工单编号是 {reference}，请确认。', records)
    print('\nB：独立请求只发送问题。')
    ask(backend, independent, question, records)
    print('\nC：应用把 A 的历史放回请求，再问同一个问题。')
    ask(backend, saved, question, records)
    import re
    identifiers = lambda text: set(re.findall(r'(?<![A-Za-z0-9-])WS-[A-Za-z0-9-]+(?![A-Za-z0-9-])', text))
    checks = {
        'independent_request_has_no_reference': all(reference not in m['content'] for m in records[1]['messages']),
        'history_request_contains_reference': any(reference in m['content'] for m in records[2]['messages']),
        'independent_answer_abstains': '资料不足' in records[1]['answer'] and not identifiers(records[1]['answer']),
        'history_answer_uses_current_reference': identifiers(records[2]['answer']) == {reference},
    }
    return {'model': backend.model, 'reference': reference, 'cases': dict(zip('ABC', records)),
            'checks': checks, 'passed': all(checks.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", default="WS-4827", help="本次教学工单号")
    parser.add_argument('--output', type=Path, help='保存三次实际请求、回复、用量与闭集事实检查')
    args = parser.parse_args()
    import re
    if not re.fullmatch(r'WS-[A-Za-z0-9-]+', args.reference):
        parser.error('工单号使用 WS- 前缀及英文字母、数字或连字符。')
    backend = DeepSeek()
    # 用户凭据仅由客户端读取，不进入教学消息或输出。
    print(f"服务地址：{backend.client.base_url}；模型：{backend.model}")
    result = run_experiment(backend, args.reference)
    for name, passed in result['checks'].items():
        print(f"{'通过' if passed else '未通过'}：{name}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'实际请求与结果：{args.output}')
    if not result['passed']:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
