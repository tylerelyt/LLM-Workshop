"""Translate a Fibonacci generator and compare its Python and JavaScript behavior."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


import argparse
import json
import re
import subprocess


def fibonacci(count):
    a, b = 0, 1
    while count > 0:
        yield a
        a, b = b, a + b
        count -= 1


def python_program(count):
    return f"""def fibonacci(n):
    a, b = 0, 1
    while n > 0:
        yield a
        a, b = b, a + b
        n -= 1

for number in fibonacci({count}):
    print(number)
"""


def translate_code_to_js(python_code):
    from workshop_runtime.chat import chat

    prompt = (
        "将下面的 Python 程序转换为 JavaScript，保留生成器的初始值、更新顺序和终止条件。"
        "定义同名的 function* fibonacci(n)，并保留打印示例。"
        "仅返回一个 javascript 代码块，使用标准语言语法，不导入模块、不访问文件或网络。\n\n"
        f"Python 程序：\n{python_code}"
    )
    response = chat(messages=[{"role": "user", "content": prompt}])
    answer = response
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("模型没有返回转换结果。")
    return answer


def extract_javascript(answer):
    fence = chr(96) * 3
    blocks = re.findall(fence + r"(?:javascript|js)\s*\n(.*?)" + fence, answer, re.DOTALL | re.IGNORECASE)
    if len(blocks) == 1:
        return blocks[0].strip() + "\n"
    if fence not in answer:
        return answer.strip() + "\n"
    raise ValueError("需要一个完整的 javascript 代码块，先检查模型输出。")


# Each input loads the inspected source in a new context, then calls fibonacci.
NODE_CHECK = """
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const counts = JSON.parse(process.argv[2]);
const results = counts.map(count => {
  const context = vm.createContext({console: {log: () => {}}});
  vm.runInContext(source, context, {timeout: 1000});
  return vm.runInContext('Array.from(fibonacci(' + count + '))', context, {timeout: 1000});
});
console.log(JSON.stringify(results));
"""


def check_javascript(path, count):
    counts = list(dict.fromkeys([0, 1, count, count + 1]))
    try:
        result = subprocess.run(
            ["node", "-e", NODE_CHECK, str(path.resolve()), json.dumps(counts)],
            capture_output=True, text=True, timeout=8, check=True,
        )
        actual = json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError("语义对照需要 Node.js，请先安装并确认 node --version 可运行。") from None
    except subprocess.TimeoutExpired:
        raise RuntimeError("JavaScript 执行超时，请检查循环终止条件。") from None
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"JavaScript 执行失败：\n{error.stderr}") from None
    except json.JSONDecodeError:
        raise RuntimeError("JavaScript 没有返回可核对的结果。") from None

    if not isinstance(actual, list) or len(actual) != len(counts):
        raise RuntimeError("JavaScript 结果数量不匹配。")
    passed = True
    for size, values in zip(counts, actual):
        expected = list(fibonacci(size))
        correct = (
            isinstance(values, list)
            and all(type(value) is int for value in values)
            and values == expected
        )
        print(f"n={size}  Python={expected}  JavaScript={values}  一致={correct}")
        passed = passed and correct
    if not passed:
        raise RuntimeError("两种语言的行为不一致，请检查初始值、更新顺序和终止条件。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5, choices=range(0, 31), metavar="0-30")
    parser.add_argument("--output", type=Path, help="Save the translated JavaScript for inspection")
    parser.add_argument("--check", type=Path, help="Execute an inspected JavaScript file and compare behavior")
    args = parser.parse_args()
    if args.check:
        try:
            check_javascript(args.check, args.count)
        except RuntimeError as error:
            parser.exit(1, f"{error}\n")
        return

    source = python_program(args.count)
    print(f"Python 程序：\n{source}\nPython 输出：{list(fibonacci(args.count))}", flush=True)
    try:
        answer = translate_code_to_js(source)
        print(f"\n模型转换结果：\n{answer}", flush=True)
        if args.output:
            code = extract_javascript(answer)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(code, encoding="utf-8")
            print(f"已保存到 {args.output}。检查代码后，使用 --check 对照实际行为。")
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f"转换失败。{error}\n")


if __name__ == "__main__":
    main()
