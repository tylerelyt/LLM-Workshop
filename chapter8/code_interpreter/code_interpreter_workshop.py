#!/usr/bin/env python3
"""Generate a knapsack program, then verify actual Docker execution when requested."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import load_environment


import argparse
import ast
from importlib.util import find_spec
import itertools
import json
import os
from pathlib import Path
import re

from autogen import AssistantAgent, UserProxyAgent
from autogen.code_utils import is_docker_running


ITEMS = ((2, 3), (3, 4), (4, 5), (5, 6), (1, 2))


def reference_solution(capacity):
    """Independent enumeration of the five teaching items."""
    best = {"selected_items": [], "total_weight": 0, "max_value": 0}
    for size in range(len(ITEMS) + 1):
        for indices in itertools.combinations(range(len(ITEMS)), size):
            weight = sum(ITEMS[index][0] for index in indices)
            value = sum(ITEMS[index][1] for index in indices)
            if weight <= capacity and value > best["max_value"]:
                best = {
                    "selected_items": [index + 1 for index in indices],
                    "total_weight": weight,
                    "max_value": value,
                }
    return best


def task_prompt(capacity):
    items = "\n".join(
        f"物品{number}: 重量{weight}kg, 价值{value}元"
        for number, (weight, value) in enumerate(ITEMS, 1)
    )
    return (
        f"背包容量为{capacity}kg，每件物品最多选一次，求能获得的最大价值。\n\n"
        f"{items}\n\n"
        "请编写完整可运行的 Python 程序，打印最优物品组合、总重量和最大价值。"
        "最后额外输出一行 RESULT_JSON= 加一个 JSON 对象，"
        "对象字段为 selected_items（物品编号数组）、total_weight（总重量）、max_value（总价值）。"
        "把程序放在一个 python 代码块中，使用标准库，勿写入文件或访问网络。"
    )


def get_llm_config():
    load_environment()
    compatible = bool(os.getenv("OPENAI_API_KEY"))
    api_key = os.getenv("OPENAI_API_KEY") if compatible else os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请配置 OPENAI_API_KEY 和 OPENAI_MODEL，或设置 DASHSCOPE_API_KEY。")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini") if compatible else os.getenv("LLM_MODEL", "qwen-max")
    base_url = (
        os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    ) if compatible else "https://dashscope.aliyuncs.com/compatible-mode/v1"
    return {
        "config_list": [{"model": model, "api_key": api_key, "base_url": base_url}],
        "temperature": 0.3,
    }


class RecordingExecutor(UserProxyAgent):
    """Keep outputs returned by the executor independently of model commentary."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execution_records = []

    def run_code(self, code, **kwargs):
        exit_code, output, image = super().run_code(code, **kwargs)
        self.execution_records.append({"exit_code": exit_code, "output": output})
        return exit_code, output, image


def create_code_interpreter(execute=False, output_dir="workspace"):
    assistant = AssistantAgent(name="Assistant", llm_config=get_llm_config())
    executor = RecordingExecutor(
        name="Executor",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=4,
        is_termination_msg=lambda msg: (msg.get("content") or "").strip().lower() in ["terminate", "exit", "done"],
        code_execution_config={"work_dir": str(output_dir), "use_docker": True} if execute else False,
    )
    return assistant, executor


def verify_execution(records, capacity):
    if not records:
        raise RuntimeError("没有实际代码执行记录，尚不能验收执行结果。")
    record = records[-1]
    if record["exit_code"] != 0:
        raise RuntimeError("最后一次执行失败，请查看容器输出与后续修正。")
    result_lines = re.findall(r"^RESULT_JSON=(.+)$", record["output"], re.MULTILINE)
    if len(result_lines) != 1:
        raise RuntimeError("实际执行输出中缺少唯一的 RESULT_JSON 结果行。")
    try:
        result = json.loads(result_lines[0])
    except json.JSONDecodeError:
        raise RuntimeError("实际执行输出中的 RESULT_JSON 不是合法 JSON。") from None
    if not isinstance(result, dict):
        raise RuntimeError("执行结果应为一个 JSON 对象。")
    selected = result.get("selected_items")
    if (
        not isinstance(selected, list)
        or not all(type(number) is int and 1 <= number <= len(ITEMS) for number in selected)
        or len(selected) != len(set(selected))
    ):
        raise RuntimeError("所选物品编号无效或重复。")
    weight = sum(ITEMS[number - 1][0] for number in selected)
    value = sum(ITEMS[number - 1][1] for number in selected)
    if (
        weight > capacity
        or result.get("total_weight") != weight
        or result.get("max_value") != value
        or value != reference_solution(capacity)["max_value"]
    ):
        raise RuntimeError("实际执行结果未同时满足容量、组合总计和最优价值，请核对算法。")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Run generated code in Docker")
    parser.add_argument("--capacity", type=int, choices=range(1, 16), default=10, metavar="1-15")
    parser.add_argument("--output-dir", type=Path, default=Path("workspace"))
    parser.add_argument("--show-task", action="store_true", help="Inspect teaching data and reference without a model call")
    args = parser.parse_args()
    task = task_prompt(args.capacity)
    print(f"任务：\n{task}", flush=True)
    if args.show_task:
        print("独立枚举参考结果：", json.dumps(reference_solution(args.capacity), ensure_ascii=False))
        return

    if args.execute:
        if find_spec("docker") is None:
            parser.error("缺少 Docker Python SDK。请在仓库根目录运行 python -m pip install -r chapter8/code_interpreter/requirements.txt。")
        if not is_docker_running():
            parser.error("无法连接 Docker。请启动 Docker 并运行 docker info 检查连接。如果 CLI 已连通，请核对 DOCKER_HOST。")
    try:
        assistant, executor = create_code_interpreter(args.execute, args.output_dir)
    except ValueError as error:
        parser.error(str(error))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.output_dir / "report.json"
    report = {"capacity": args.capacity, "mode": "docker" if args.execute else "generation"}

    if args.execute:
        executor.initiate_chat(assistant, message=task, max_turns=6)
        report["executions"] = executor.execution_records
        try:
            report["verified_result"] = verify_execution(executor.execution_records, args.capacity)
        except RuntimeError as error:
            report["status"] = "execution_unverified"
            report["error"] = str(error)
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            parser.exit(1, f"{error}\n执行记录：{report_path}\n")
        report["status"] = "execution_verified"
        print("已根据实际执行输出核对物品组合、重量和最优价值。")
    else:
        result = executor.initiate_chat(assistant, message=task, max_turns=1)
        fence = chr(96) * 3
        code = re.search(fence + r"python\s*(.*?)" + fence, result.summary or "", re.DOTALL)
        if not code:
            parser.exit(1, "模型没有返回可检查的 Python 代码块。\n")
        program = code.group(1).rstrip() + "\n"
        try:
            ast.parse(program)
        except SyntaxError as error:
            parser.exit(1, f"生成代码存在语法错误。{error}\n")
        output = args.output_dir / "knapsack_generated.py"
        output.write_text(program, encoding="utf-8")
        report.update({"status": "generated_only", "code_file": str(output)})
        print(f"已生成 {output}，本轮尚未执行。检查代码后，用 --execute 发起新的生成和执行流程。")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"运行记录：{report_path}")


if __name__ == "__main__":
    main()
