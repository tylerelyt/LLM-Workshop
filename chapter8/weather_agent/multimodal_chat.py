
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import os

import requests
from workshop_runtime.langchain_llm import WorkshopLLM
from langchain.agents import initialize_agent
from langchain.tools import Tool

# 高德API的基本信息
AMAP_KEY = os.getenv("AMAP_API_KEY")
AMAP_BASE_URL = 'https://restapi.amap.com/v3'


# 获取城市编码的工具
def get_city_code(city_name):
    if not AMAP_KEY:
        city_name = city_name.strip().strip("\"'").removesuffix("市")
        return "110000" if city_name == "北京" else {"error": "教学样例只包含北京"}
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
    if "error" in response:
        return response
    if response.get('status') == '1':
        districts = response.get('districts', [])
        if districts:
            city_info = districts[0]
            # 城市查询应使用城市自身的编码，不能被第一个下级行政区覆盖。
            if city_info.get('adcode'):
                return city_info['adcode']
    return {"error": f"无法获取城市编码: {response.get('info', '未知错误')}"}



# 获取天气数据的工具
def get_weather_data(city_code, forecast=False):
    if not AMAP_KEY:
        if city_code.strip().strip('"').strip("'") != "110000":
            return {"error": "教学样例只包含北京的城市编码 110000"}
        return {"source": "教学样例", "city": "北京", "weather": "多云", "temperature": "18℃"}
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
        res = requests.get(url=url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        if data.get('status') == '1':
            return data
        return {"error": f"请求失败: {data.get('info', '未知错误')}"}
    except (requests.RequestException, ValueError):
        return {"error": "高德请求失败，请检查网络和 AMAP_API_KEY"}


OPEN_METEO_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
WEATHER_LABELS = {
    0: "晴朗", 1: "大致晴朗", 2: "局部多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "强毛毛雨",
    56: "轻冻毛毛雨", 57: "强冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨", 66: "小冻雨", 67: "强冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "小阵雨", 81: "阵雨", 82: "强阵雨", 85: "小阵雪", 86: "强阵雪",
    95: "雷暴", 96: "雷暴伴小冰雹", 99: "雷暴伴强冰雹",
}


def get_city_coordinates(city_name):
    city_name = city_name.strip().strip("\"'").removesuffix("市")
    try:
        response = requests.get(OPEN_METEO_GEOCODING, params={
            "name": city_name, "countryCode": "CN", "count": 1, "language": "zh",
        }, timeout=15)
        response.raise_for_status()
        locations = response.json().get("results", [])
        if locations:
            city = locations[0]
            return f"{city['latitude']},{city['longitude']}"
    except (requests.RequestException, ValueError, KeyError):
        return {"error": "Open-Meteo 城市查询失败"}
    return {"error": f"Open-Meteo 未找到城市：{city_name}"}


def get_open_meteo_weather(coordinates):
    try:
        latitude, longitude = map(float, coordinates.strip().strip("\"'").split(","))
    except ValueError:
        return {"error": "请输入城市查询返回的纬度,经度"}
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return {"error": "经纬度超出范围"}

    try:
        response = requests.get(OPEN_METEO_FORECAST, params={
            "latitude": latitude, "longitude": longitude,
            "current": "temperature_2m,weather_code", "timezone": "auto",
        }, timeout=15)
        response.raise_for_status()
        data = response.json()
        current = data["current"]
        code = current["weather_code"]
        return {
            "source": "Open-Meteo（天气模型）",
            "time": current["time"],
            "timezone": data["timezone"],
            "temperature": current["temperature_2m"],
            "temperature_unit": data["current_units"]["temperature_2m"],
            "weather_code": code,
            "weather": WEATHER_LABELS.get(code, "未知"),
        }
    except (requests.RequestException, ValueError, KeyError):
        return {"error": "Open-Meteo 天气查询失败"}


def main():
    parser = argparse.ArgumentParser(description="先定位城市，再查询天气。")
    parser.add_argument("--live", action="store_true", help="使用 Open-Meteo，无需天气 API key")
    parser.add_argument("--city", default="北京", help="城市名；固定教学样例只包含北京")
    args = parser.parse_args()

    if args.live:
        location_tool = Tool(
            name="GetCityCoordinates", func=get_city_coordinates,
            description="把城市名转成纬度,经度。只传中文城市名，例如：北京",
        )
        weather_tool = Tool(
            name="GetWeather", func=get_open_meteo_weather,
            description="查询当地天气模型的当前结果。参数是 GetCityCoordinates 返回的纬度,经度",
        )
        print("数据来源：Open-Meteo。")
    else:
        location_tool = Tool(
            name="GetCityCode", func=get_city_code,
            description="根据中文城市名获取城市编码，例如：北京",
        )
        weather_tool = Tool(
            name="GetWeather", func=get_weather_data,
            description="根据 GetCityCode 返回的城市编码查询当前天气。只传城市编码",
        )
        print("数据来源：高德。" if AMAP_KEY else "数据来源：固定教学样例（非实时天气）。")

    agent = initialize_agent(
        tools=[location_tool, weather_tool], llm=WorkshopLLM(),
        agent_type="zero-shot-react-description", verbose=True, handle_parsing_errors=True,
    )
    question = f"{args.city}的天气怎么样？"
    print(f"用户问题：{question}")
    result = agent.invoke({"input": (
        f"{question} 先调用 {location_tool.name}，再把它返回的值传给 GetWeather。"
        "根据工具返回的数据作答。工具失败时说明原因。"
    )})["output"]
    if args.live or AMAP_KEY:
        print(result)
    else:
        print(f"教学样例（非实时天气）：{result}")


if __name__ == "__main__":
    main()
