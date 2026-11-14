
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import json

from langchain.chains import LLMChain, SequentialChain
from workshop_runtime.langchain_llm import WorkshopLLM
from langchain.prompts import PromptTemplate

# 创建 LLM 实例
llm = WorkshopLLM()

def create_chain(template: str, input_vars: list, output_key: str) -> LLMChain:
    """创建 LLMChain 实例"""
    prompt = PromptTemplate(
        input_variables=input_vars,
        template=template
    )
    return LLMChain(llm=llm, prompt=prompt, output_key=output_key)

# 第一步：头脑风暴解决方案
template_step1 = """
步骤 1:
我面临一个关于{input}的问题。请提供三个不同的解决方案，考虑到以下因素：{perfect_factors}。
A:
"""
chain1 = create_chain(template_step1, ["input", "perfect_factors"], "solutions")

# 第二步：评估解决方案
template_step2 = """
步骤 2:
请评估以下解决方案的优缺点、实施难度和预期结果，并为每个方案分配成功概率和信心水平。
原任务：{input}
原始约束：{perfect_factors}
上一步产物：
{solutions}
A:
"""
chain2 = create_chain(template_step2, ["solutions", "input", "perfect_factors"], "review")

# 第三步：深化思考过程
template_step3 = """
步骤 3:
请深入分析每个解决方案，提供实施策略、所需资源和潜在障碍，同时考虑意外结果及应对措施。
原任务：{input}
原始约束：{perfect_factors}
上一步产物：
{review}
A:
"""
chain3 = create_chain(template_step3, ["review", "input", "perfect_factors"], "deepen_thought_process")

# 第四步：排序解决方案
template_step4 = """
步骤 4:
根据评估和分析结果，对解决方案进行排序，说明理由，并给出最终考虑。
原任务：{input}
原始约束：{perfect_factors}
上一步产物：
{deepen_thought_process}
A:
"""
chain4 = create_chain(template_step4, ["deepen_thought_process", "input", "perfect_factors"], "ranked_solutions")

# 将各个链条连接起来
overall_chain = SequentialChain(
    chains=[chain1, chain2, chain3, chain4],
    input_variables=["input", "perfect_factors"],
    output_variables=["solutions", "review", "deepen_thought_process", "ranked_solutions"],
    verbose=True
)

def main():
    parser = argparse.ArgumentParser(description="跟踪固定四步工作流的中间变量。")
    parser.add_argument("--problem", default="为20人团队设计可追溯的内部知识问答原型")
    parser.add_argument("--constraints", default="仅使用公开教学资料；答案提供原文出处；资料不足时拒答；本轮不训练模型")
    parser.add_argument("--output", type=Path, help="保存实际输入约束和四个阶段的产物")
    args = parser.parse_args()
    result = overall_chain.invoke({"input": args.problem, "perfect_factors": args.constraints})
    for name, title in [('solutions', '生成候选'), ('review', '评估约束'), ('deepen_thought_process', '深化方案'), ('ranked_solutions', '排序与理由')]:
        print(f"\n=== {title} ===\n{result[name]}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"完整输入与产物：{args.output}")


if __name__ == "__main__":
    main()
