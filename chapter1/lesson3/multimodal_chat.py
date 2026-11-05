from langchain_ollama.llms import OllamaLLM
from langchain.agents import initialize_agent
from langchain.tools import Tool
import requests

# 高德API的基本信息
AMAP_KEY = 'YOUR KEY'  # 替换为你的高德应用 key
AMAP_BASE_URL = 'https://restapi.amap.com/v3'


# 获取城市编码的工具
def get_city_code(city_name):
    url = f'{AMAP_BASE_URL}/config/district'
    params = {
        'key': AMAP_KEY,
        'keywords': city_name,
        'subdistrict': 2,
    }
    response = fetch_data(url, params)
    return parse_city_code_response(response)


# 解析城市编码返回值
def parse_city_code_response(response):
    if response.get('status') == '1':
        districts = response.get('districts', [])
        if districts:
            # 假设 adcode 在第一个 district 中
            city_info = districts[0]
            adcode = city_info.get('adcode', '未知')

            # 如果需要进一步查找 adcode，可以遍历下级行政区
            if 'districts' in city_info:
                for district in city_info['districts']:
                    if 'adcode' in district:
                        adcode = district['adcode']  # 更新为子级的 adcode
                        break

            return adcode
    return {"error": f"无法获取城市编码: {response.get('info', '未知错误')}"}



# 获取天气数据的工具
def get_weather_data(city_code, forecast=False):
    url = f'{AMAP_BASE_URL}/weather/weatherInfo'
    params = {
        'key': AMAP_KEY,
        'city': city_code,
        'extensions': 'all' if forecast else 'base'
    }
    response = fetch_data(url, params)
    return response


# 封装API请求逻辑
def fetch_data(url, params):
    try:
        res = requests.get(url=url, params=params)
        data = res.json()
        if data.get('status') == '1':
            return data
        return {"error": f"请求失败: {data.get('info', '未知错误')}"}
    except Exception as e:
        return {"error": f"请求时出错: {str(e)}"}


# 定义获取城市编码的工具
city_code_tool = Tool(
    name="GetCityCode",
    func=get_city_code,
    description="根据城市名称获取对应的城市编码，参数是中文城市名称，例如：上海"
)


# 定义获取天气的工具
weather_tool = Tool(
    name="GetWeather",
    func=get_weather_data,
    description="获取指定城市的天气信息，参数是城市编码和是否需要预报"
)


# 初始化 LLM
llm = OllamaLLM(model="llama3")


# 定义 agent
agent = initialize_agent(
    tools=[city_code_tool, weather_tool],  # 使用自定义工具
    llm=llm, 
    agent_type="zero-shot-react-description", 
    verbose=True,
    agent_kwargs={"handle_parsing_errors": True}
)


# 用户问题
user_question = "北京的天气怎么样？"
print(f"用户问题：{user_question}")


# 执行并打印结果
response = agent.run(user_question)
print(response)
