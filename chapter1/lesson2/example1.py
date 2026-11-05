from langchain_ollama.llms import OllamaLLM
from langchain.agents import load_tools, initialize_agent
from langchain.tools import Tool
import numexpr as ne

# 定义数学计算工具
def calculate_expression(expression):
    return ne.evaluate(expression).item()  # 使用 numexpr 计算表达式并返回结果

math_tools = [
    Tool(
        name="Numexpr Math",
        func=calculate_expression,
        description="一个能够进行高效数学计算的工具，参数是输入的数学表达式"
    )
]

# 初始化 LLM
llm = OllamaLLM(model="llama3")

# 定义 agent
agent = initialize_agent(
    tools=math_tools,  # 使用自定义的数学计算工具
    llm=llm, 
    agent_type="zero-shot-react-description", 
    verbose=True,
    agent_kwargs={"handle_parsing_errors": True}  # 处理解析错误
)

# 用户问题
user_question = "What is 37593 * 67?"
print(f"用户问题：{user_question}")

# 执行并打印结果
response = agent.run(user_question)
print(response)
