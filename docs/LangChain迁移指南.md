# LangChain 迁移指南

## 概述

本项目已将 LLM 客户端迁移到 LangChain 框架,以获得更强大的功能、更好的抽象和更易于扩展的架构。

## 主要变更

### 1. 核心架构

**之前**: 直接使用 OpenAI SDK
```python
from openai import OpenAI
client = OpenAI(api_key=...)
```

**现在**: 使用 LangChain 的抽象接口
```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(api_key=...)
```

### 2. 消息格式

LangChain 使用特定的消息类:

| 旧格式 | LangChain 格式 |
|--------|---------------|
| `{"role": "system", "content": "..."}` | `SystemMessage(content="...")` |
| `{"role": "user", "content": "..."}` | `HumanMessage(content="...")` |
| `{"role": "assistant", "content": "..."}` | `AIMessage(content="...")` |

### 3. 兼容性

为保持向后兼容,`LangChainLLMClient` 提供了 `_convert_messages()` 方法自动转换格式。

## 使用示例

### 基础调用

```python
from models.llm_client import LLMClientFactory

# 创建客户端
client = LLMClientFactory.create_client(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4o",
    temperature=0.1
)

# 聊天
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
]
response = client.chat(messages)
print(response)
```

### 结构化数据提取

```python
import json

schema = {
    "井号": "",
    "井深": 0,
    "井类型": ""
}

messages = [
    {"role": "user", "content": "从以下文本中提取井信息..."}
]

result = client.extract_structured(messages, schema)
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 异步调用

```python
import asyncio

async def async_example():
    client = LLMClientFactory.create_client(
        provider="openai",
        api_key="your-api-key"
    )

    messages = [
        {"role": "user", "content": "你好"}
    ]

    response = await client.achat(messages)
    print(response)

asyncio.run(async_example())
```

## 支持的 LLM 提供商

| 提供商 | 类名 | 默认模型 | 默认 Base URL |
|--------|------|---------|--------------|
| OpenAI | `OpenAIClient` | gpt-4o | https://api.openai.com/v1 |
| DeepSeek | `DeepSeekClient` | deepseek-chat | https://api.deepseek.com/v1 |
| Qwen | `QwenClient` | qwen-plus | https://dashscope.aliyuncs.com/compatible-mode/v1 |

## 配置选项

### 初始化参数

```python
client = LangChainLLMClient(
    api_key="your-api-key",           # 必需: API 密钥
    base_url="https://...",            # 可选: API 基础 URL
    model="gpt-4o",                   # 可选: 模型名称
    temperature=0.1,                 # 可选: 温度 (0-1)
    max_tokens=4000,                  # 可选: 最大 token 数
    timeout=60,                       # 可选: 超时时间(秒)
    streaming=False                   # 可选: 是否启用流式输出
)
```

### 调用参数

```python
response = client.chat(
    messages=[...],
    temperature=0.5,      # 覆盖默认值
    max_tokens=2000,       # 覆盖默认值
    # 其他 LangChain 参数...
)
```

## LangChain 高级功能

### 1. 直接访问 LangChain LLM 对象

```python
from langchain_core.messages import HumanMessage, SystemMessage

client = LLMClientFactory.create_client(...)
llm = client.llm  # 直接访问 LangChain LLM 对象

# 使用 LangChain 原生方式调用
messages = [
    SystemMessage(content="你是一个助手"),
    HumanMessage(content="你好")
]
response = llm.invoke(messages)
print(response.content)
```

### 2. 与 LangChain 链集成

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}"),
    ("user", "{input}")
])

chain = prompt | client.llm | StrOutputParser()
result = chain.invoke({"role": "助手", "input": "你好"})
```

### 3. 流式输出

```python
# 启用流式输出
client = LangChainLLMClient(
    api_key="your-api-key",
    streaming=True
)

# 使用流式输出
for chunk in client.llm.stream(messages):
    print(chunk.content, end="")
```

## 错误处理

所有错误都会抛出 `LLMError` 异常:

```python
from utils.exceptions import LLMError

try:
    response = client.chat(messages)
except LLMError as e:
    print(f"LLM 调用失败: {e}")
```

## 性能优化

### 1. 缓存

LangChain 支持缓存,可以减少重复调用:

```python
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

set_llm_cache(InMemoryCache())
```

### 2. 批量调用

```python
from langchain_core.messages import HumanMessage

# 批量调用
responses = client.llm.batch([
    [HumanMessage(content="问题1")],
    [HumanMessage(content="问题2")],
    [HumanMessage(content="问题3")]
])
```

### 3. 并行调用

使用异步接口提高性能:

```python
import asyncio

async def process_multiple():
    tasks = [
        client.achat([{"role": "user", "content": f"问题{i}"}])
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks)
    return results

results = asyncio.run(process_multiple())
```

## 依赖安装

确保安装了 LangChain 相关依赖:

```bash
pip install langchain==0.1.0
pip install langchain-core==0.1.10
pip install langchain-openai==0.0.2
```

或在 requirements.txt 中包含:

```txt
langchain==0.1.0
langchain-core==0.1.10
langchain-openai==0.0.2
```

## 迁移检查清单

- [x] 已更新 `models/llm_client.py` 使用 LangChain
- [x] 已更新 `requirements.txt` 添加 LangChain 依赖
- [x] 保持向后兼容的 API 接口
- [x] 添加异步支持 (`achat` 方法)
- [x] 支持直接访问 LangChain LLM 对象

## 常见问题

### Q: 如何使用自定义的 LangChain LLM?

A: 可以直接访问 `client.llm` 属性:

```python
custom_llm = client.llm  # ChatOpenAI 实例
```

### Q: 如何使用 LangChain 的输出解析器?

A: 结合 LangChain 的链使用:

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
chain = client.llm | parser
result = chain.invoke(messages)
```

### Q: 异步接口如何使用?

A: 使用 `client.achat()` 方法:

```python
response = await client.achat(messages)
```

### Q: 是否支持流式输出?

A: 支持,在初始化时设置 `streaming=True`:

```python
client = LangChainLLMClient(streaming=True)
```

## 未来扩展

使用 LangChain 后,可以轻松扩展更多功能:

1. **向量存储集成**: 使用 LangChain 的向量数据库
2. **RAG 实现**: 轻松实现检索增强生成
3. **工具调用**: 使用 LangChain 的工具调用功能
4. **智能体**: 构建更复杂的智能体应用
5. **记忆管理**: 使用 LangChain 的记忆组件

## 参考

- [LangChain 官方文档](https://python.langchain.com/)
- [LangChain OpenAI 集成](https://python.langchain.com/docs/integrations/chat/openai/)
- [Chat 模型](https://python.langchain.com/docs/modules/model_io/chat/)
