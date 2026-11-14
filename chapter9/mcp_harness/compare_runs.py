"""同一编程任务的三组对照：固定模型改 Harness，再固定 Harness 换模型。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import load_environment, uses_openai_config

LESSON = Path(__file__).resolve().parent
TASK = "检查 calculator.py，先运行测试，再修复普通除法的小数结果错误，保留零除异常，并补充负数测试后重跑。"
# 核验代码由本程序提供，放在目标工作区之外；模型修改随课测试不能改变它。
CHECK = '''import sys
sys.path.insert(0, sys.argv[1])
from calculator import divide
assert divide(7, 2) == 3.5
assert divide(-7, 2) == -3.5
assert divide(6, 3) == 2
try:
    divide(1, 0)
except ZeroDivisionError:
    pass
else:
    raise AssertionError("应保留零除异常")
print("小数、负数、整数与零除行为均通过")
'''


def check_project(workspace, checker_dir):
    result = subprocess.run([sys.executable, '-I', '-c', CHECK, str(workspace)],
                            cwd=checker_dir, capture_output=True, text=True, timeout=30)
    return {'passed': result.returncode == 0, 'exit_code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nanocode', type=Path, required=True)
    parser.add_argument('--models', nargs=2, required=True, metavar=('MODEL_A', 'MODEL_B'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-steps', type=int, default=12)
    parser.add_argument('--yes', action='store_true', help='三组均自动批准工具；默认逐次询问')
    args = parser.parse_args()
    args.models = [model.strip() for model in args.models]
    if not args.nanocode.is_file() or args.max_steps < 1 or not all(args.models) or args.models[0] == args.models[1]:
        parser.error('需要有效的 nanocode.py、正数步数和两个不同的模型 ID。')
    load_environment()
    model_key = 'OPENAI_MODEL' if uses_openai_config() else 'DEEPSEEK_MODEL'
    args.out.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='comparison-', dir=args.out.resolve()))
    source = LESSON / 'example_project'
    names = ('calculator.py', 'test_calculator.py', 'AGENTS.md')
    initial_files = {name: (source / name).read_bytes() for name in names}
    source_hash = hashlib.sha256(b''.join(initial_files.values())).hexdigest()
    profiles = [('A', args.models[0], False), ('B', args.models[0], True), ('C', args.models[1], False)]
    report = {'task': TASK, 'source_sha256': source_hash, 'runs': []}
    for name, model, read_only in profiles:
        workspace = directory / name
        workspace.mkdir()
        for filename, content in initial_files.items():
            (workspace / filename).write_bytes(content)
        print(f'\n=== {name} · Model={model} · Harness 只读={read_only} ===', flush=True)
        before = check_project(workspace, directory)
        command = [sys.executable, str(LESSON / 'cli_agent.py'), TASK,
                   '--nanocode', str(args.nanocode.resolve()), '--workspace', str(workspace),
                   '--max-steps', str(args.max_steps)]
        if read_only:
            command.append('--read-only')
        if args.yes:
            command.append('--yes')
        # 继承终端，批准请求仍然可见；每组使用全新的目标副本和会话。
        result = subprocess.run(command, env={**os.environ, model_key: model})
        after = check_project(workspace, directory)
        state_path = workspace / '.agent' / 'context.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else None
        session = state['sessions'][state['current']] if state and state['current'] else {}
        row = {'case': name, 'model': model, 'source_sha256': source_hash,
               'generation': {'thinking': False, 'max_tokens': 4096, 'sampling': 'service_default'},
               'harness': {'read_only': read_only, 'max_steps': args.max_steps,
               'auto_approve': args.yes}, 'workspace': str(workspace), 'agent_exit': result.returncode,
               'before': before, 'after': after,
               'model_replies': sum(m['role'] == 'assistant' for m in session.get('history', [])),
               'tool_observations': len(session.get('observations', []))}
        report['runs'].append(row)
        (directory / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"{name}：独立核验 {before['passed']} → {after['passed']}；模型回复 {row['model_replies']} 次；工具观察 {row['tool_observations']} 条", flush=True)
    print('\n对照：A/B 只改变 Harness 的只读策略；A/C 只改变模型。')
    print('模型结束回答与任务完成分开判断；一次采样不证明模型或策略稳定更好。')
    print(f'完整会话、代码副本和核验结果：{directory}')
    return int(any(row['agent_exit'] not in (0, 2) for row in report['runs']))


if __name__ == '__main__':
    raise SystemExit(main())
