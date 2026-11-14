
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import re

from workshop_runtime.chat import chat


def decompose_task(task_description):
    """将任务描述分解为可操作的步骤"""
    prompt = f"请将以下任务分解成三个操作步骤。每行以数字和句点开头，只输出步骤，不计算结果。\n{task_description}"
    response = chat(messages=[
        {'role': 'user', 'content': prompt},
    ])
    steps = re.findall(r"^\s*(\d+)[.、)]\s*(\S.*)$", response, re.MULTILINE)
    if [number for number, _ in steps] != ["1", "2", "3"]:
        raise ValueError("模型未返回三个编号步骤，请重试。")
    return [step for _, step in steps]


def check_result(task, step, response):
    """检查本步结果是否正确且符合原任务。"""
    prompt = (
        f"原任务：{task}\n待检查的步骤：{step}\n候选结果：{response}\n"
        "候选结果必须正确完成这一步。只输出 PASS 或 FAIL。"
    )
    validation_response = chat(messages=[
        {'role': 'user', 'content': prompt},
    ])
    content = validation_response
    verdict = content.strip().strip("`*。.！!").upper()
    print(f"检查结果：{verdict}")
    return verdict == "PASS"


def combine_results(results):
    """综合所有有效结果"""
    prompt = "用以下通过检查的结果给出最终结论，不添加其他假设：\n" + "\n".join(results)
    summary_response = chat(messages=[
        {'role': 'user', 'content': prompt},
    ])
    content = summary_response
    return content


def reasoning_with_checkpoints(task_description, inject_error=False):
    """多步骤推理中的检查机制"""
    steps = decompose_task(task_description)
    results = []

    for index, step in enumerate(steps, 1):
        prior = "\n".join(results) or "无"
        prompt = (
            f"原任务：{task_description}\n已确认的结果：\n{prior}\n"
            f"现在只完成这一步：{step}\n用一两句话给出算式和结果。"
        )
        response = chat(messages=[{'role': 'user', 'content': prompt}])  # 生成模型响应
        if inject_error and index == 2:
            response = "含备用的总量是 26 套。"
            print("教学故障注入：将第二步候选结果改为 26 套。")
        print(f"\n步骤 {index}：{step}\n候选结果：{response}")
        if not check_result(task_description, step, response):
            raise ValueError(f"步骤 {index} 未通过检查：{step}")
        results.append(response)

    return combine_results(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="逐步生成候选结果，检查通过后才继续。")
    parser.add_argument("--inject-error", action="store_true", help="把第二步改错，观察检查点是否拦截")
    args = parser.parse_args()
    task_description = "为工作坊准备耗材。4 张桌子各需 6 套，另外备 3 套，每套 2 元。求桌面用量、含备用的总量和费用。"
    try:
        result = reasoning_with_checkpoints(task_description, inject_error=args.inject_error)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print(f"\n最终结果：{result}")
