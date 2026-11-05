from langchain.chains import LLMChain, SequentialChain
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate

# 创建 LLM 实例
llm = OllamaLLM(model="llama3")  # 使用 Ollama 模型

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
{solutions}
A:
"""
chain2 = create_chain(template_step2, ["solutions"], "review")

# 第三步：深化思考过程
template_step3 = """
步骤 3:
请深入分析每个解决方案，提供实施策略、所需资源和潜在障碍，同时考虑意外结果及应对措施。
{review}
A:
"""
chain3 = create_chain(template_step3, ["review"], "deepen_thought_process")

# 第四步：排序解决方案
template_step4 = """
步骤 4:
根据评估和分析结果，对解决方案进行排序，说明理由，并给出最终考虑。
{deepen_thought_process}
A:
"""
chain4 = create_chain(template_step4, ["deepen_thought_process"], "ranked_solutions")

# 将各个链条连接起来
overall_chain = SequentialChain(
    chains=[chain1, chain2, chain3, chain4],
    input_variables=["input", "perfect_factors"],
    output_variables=["ranked_solutions"],
    verbose=True
)

# 示例输入
result = overall_chain({
    "input": "人类对火星的殖民",
    "perfect_factors": "地球与火星之间的距离非常遥远，使得定期补给变得困难"
})

print(result)
