<a id="lesson-3-building-a-tool-using-agent"></a>

# 天气工具 Agent

构建先解析地点、再查询天气的工具 Agent。默认使用固定教学数据观察调用链；配置真实天气服务后，再核对在线返回。

## 工程任务

天气回答依赖地点解析和外部查询。一个字段缺失时，程序仍可能生成看起来完整的回答。

在 [multimodal_chat.py](multimodal_chat.py) 中，固定地点、问题与教学数据，只在工具返回中移除一个天气字段。

说明何时应重新查询、何时应报告缺失，以及接口错误是否被误写成天气事实。

## 学习目标

- **创建工具**：定义调用外部 API 的自定义工具。
- **初始化 Agent**：创建 LangChain Agent，并为它配置自定义工具。
- **多步推理**：观察 Agent 如何先取得城市编码，再查询天气，按顺序完成请求。
- **API 接入**：对照固定教学样例与实时天气 API。

---

<a id="file-descriptions"></a>

## 文件说明

- `multimodal_chat.py`：Agent 先查询地点，再将结果传入天气工具。
- `requirements.txt`：列出本课所需的 Python 依赖。

---

<a id="setup-and-execution"></a>

## 环境准备与运行

用同一句「北京的天气怎么样？」观察 Agent 如何先查地点，再把地点工具的返回值传给天气工具。

从仓库根目录安装依赖。在另一个终端按课程说明启动模型桥接。[课程模型配置](../../README-DEEPSEEK.md)

```bash
python -m pip install -r chapter8/weather_agent/requirements.txt
python chapter8/weather_agent/multimodal_chat.py
python chapter8/weather_agent/multimodal_chat.py --live
```

未设置高德凭证时，第一遍使用固定教学数据。第二遍通过 Open-Meteo 查找北京的经纬度，再查询带时间戳的当前天气模型结果。对照两次轨迹中的 `Action Input` 和 `Observation`，确认天气工具收到的是地点工具实际返回的值。[地点查询接口](https://open-meteo.com/en/docs/geocoding-api) · [天气接口](https://open-meteo.com/en/docs)

已有高德凭证时，可在终端设置 `AMAP_API_KEY`，运行第一条 Python 命令走高德路径。

先在固定样例中只改城市，不改变模型或工具定义。

```bash
env -u AMAP_API_KEY python chapter8/weather_agent/multimodal_chat.py --city 北京
env -u AMAP_API_KEY python chapter8/weather_agent/multimodal_chat.py --city 上海
```

这两条命令只在各自进程中移除高德凭证，确保使用固定样例。北京有教学数据，上海应返回缺少样例的错误。核对 Agent 是否使用地点工具实际返回的值，以及缺少地点数据时是否说明无法查询。再使用 `--live --city 上海` 运行真实地点和天气查询时，分别核对坐标、来源与时间。真实请求可能因网络失败，应保留错误原文。

提交两条调用链，每条写出地点工具的参数和返回、天气工具收到的参数、最终答案。用这些值证明工具确实完成了数据交接；仅出现天气描述不能证明接入成功。

<a id="next-steps"></a>

## 下一步

## 在自己的项目中使用

将工具链换成自己熟悉的两步查询，先验证普通 Python 调用，再交给模型选择。注入一次缺字段或空结果，检查最终回答是否说明缺口；需要跨进程复用工具时，继续做[MCP 工具接入](../../chapter9/mcp_tools/README.md)。

[主题目录](../README.md) · [课程首页](../../README.md)
