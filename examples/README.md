# 使用示例

本目录包含项目的使用示例。

## 示例列表

### LangChain 使用示例

**文件**: `langchain_example.py`

展示如何使用 LangChain 集成的 LLM 客户端:

- ✅ 基础聊天
- ✅ 结构化数据提取
- ✅ 异步调用
- ✅ 批量处理
- ✅ 直接访问 LangChain LLM
- ✅ 使用不同提供商
- ✅ 自定义参数
- ✅ 与处理管道集成

**运行**:
```bash
cd examples
python langchain_example.py
```

**前置条件**:
1. 安装依赖: `pip install -r ../requirements.txt`
2. 配置环境变量: 在 `.env` 文件中设置 `OPENAI_API_KEY`

## 测试脚本

### LangChain 测试脚本

**文件**: `../test_langchain.py`

完整的测试套件,验证 LangChain 集成的正确性。

**运行**:
```bash
python test_langchain.py
```

**测试内容**:
- 同步聊天
- 异步聊天
- 结构化数据提取
- JSON 提取
- 直接访问 LangChain LLM
- 批量异步调用
- 不同提供商测试
- 自定义参数测试

## 文档

详细的文档请参考 `docs/` 目录:

- [LangChain 迁移指南](../docs/LangChain迁移指南.md) - 完整的迁移和使用指南
- [LangChain 使用说明](../docs/LangChain使用说明.md) - 快速开始
- [LangChain 集成总结](../docs/LangChain集成总结.md) - 集成总结

## 常见任务

### 1. 创建 LLM 客户端

```python
from models.llm_client import LLMClientFactory

client = LLMClientFactory.create_client(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4o"
)
```

### 2. 同步调用

```python
response = client.chat([
    {"role": "user", "content": "你好"}
])
```

### 3. 异步调用

```python
import asyncio

response = await client.achat([
    {"role": "user", "content": "你好"}
])
```

### 4. 结构化提取

```python
schema = {
    "字段1": "",
    "字段2": 0
}

result = client.extract_structured(messages, schema)
```

### 5. 批量处理

```python
import asyncio

tasks = [client.achat(msg) for msg in messages]
results = await asyncio.gather(*tasks)
```

## 支持的提供商

- OpenAI (gpt-4, gpt-3.5-turbo, etc.)
- DeepSeek (deepseek-chat, deepseek-coder)
- Qwen (qwen-plus, qwen-turbo, etc.)

## 更多信息

- 项目文档: [README.md](../README.md)
- API 文档: 启动服务后访问 `http://localhost:8000/docs`
- LangChain 官方文档: https://python.langchain.com/
