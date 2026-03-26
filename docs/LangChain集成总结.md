# LangChain 集成总结

## 更新时间
2026-03-23

## 更新内容

### 1. 核心模块更新

#### `models/llm_client.py`

**变更内容**:
- 从直接使用 OpenAI SDK 迁移到 LangChain 框架
- 保留 `BaseLLMClient` 基类,确保向后兼容
- 实现 `LangChainLLMClient` 作为新的客户端实现
- 添加异步支持: `achat()` 方法
- 添加消息格式转换: `_convert_messages()` 方法

**关键改进**:
```python
# 新增 LangChain 集成
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# 保持原有 API 接口
client.chat(messages)  # ✅ 兼容
client.extract_json(response)  # ✅ 兼容
client.extract_structured(messages, schema)  # ✅ 兼容

# 新增功能
await client.achat(messages)  # 🆕 异步调用
llm = client.llm  # 🆕 直接访问 LangChain 对象
```

### 2. 依赖更新

#### `requirements.txt`

**更新依赖**:
```txt
langchain==0.1.0
langchain-core==0.1.10
langchain-openai==0.0.2  # 已移除显式的 openai 包,langchain-openai 会自动安装
```

### 3. 新增文件

#### `docs/LangChain迁移指南.md`
- 详细的迁移指南
- 使用示例和最佳实践
- 常见问题解答

#### `docs/LangChain使用说明.md`
- 快速开始指南
- 主要特性说明
- 测试方法

#### `test_langchain.py`
- 完整的测试套件
- 测试同步/异步调用
- 测试不同提供商
- 测试结构化提取

## 兼容性保证

### 无需修改的文件

所有使用 `BaseLLMClient` 接口的文件都无需修改:

| 文件 | 状态 | 说明 |
|------|------|------|
| `api/app.py` | ✅ 无需修改 | 使用 `LLMClientFactory` |
| `pipeline/processor.py` | ✅ 无需修改 | 使用 `BaseLLMClient` |
| `pipeline/extractor.py` | ✅ 无需修改 | 使用 `BaseLLMClient` |
| `models/document_classifier.py` | ✅ 无需修改 | 使用 `BaseLLMClient` |

### 向后兼容的 API

所有原有 API 接口保持不变:

```python
# 创建客户端 - 完全兼容
client = LLMClientFactory.create_client(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4o"
)

# 同步调用 - 完全兼容
response = client.chat(messages)

# 结构化提取 - 完全兼容
result = client.extract_structured(messages, schema)

# JSON 提取 - 完全兼容
data = client.extract_json(response)
```

## 新功能

### 1. 异步调用

```python
import asyncio

async def process():
    response = await client.achat(messages)

asyncio.run(process())
```

### 2. 直接访问 LangChain 对象

```python
# 访问底层 LangChain LLM
llm = client.llm

# 使用 LangChain 原生方式调用
from langchain_core.messages import HumanMessage
response = llm.invoke([HumanMessage(content="你好")])
```

### 3. 流式输出支持

```python
# 启用流式输出
client = LangChainLLMClient(
    api_key="your-key",
    streaming=True
)

# 使用流式输出
for chunk in client.llm.stream(messages):
    print(chunk.content, end="")
```

### 4. 批量调用

```python
from langchain_core.messages import HumanMessage

# 批量调用
responses = client.llm.batch([
    [HumanMessage(content="问题1")],
    [HumanMessage(content="问题2")],
])
```

## 支持的提供商

| 提供商 | 客户端类 | 默认模型 | 状态 |
|--------|----------|----------|------|
| OpenAI | `OpenAIClient` | gpt-4o | ✅ 支持 |
| DeepSeek | `DeepSeekClient` | deepseek-chat | ✅ 支持 |
| Qwen | `QwenClient` | qwen-plus | ✅ 支持 |

## 迁移步骤

### 开发者迁移步骤

1. **安装新依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **运行测试**
   ```bash
   python test_langchain.py
   ```

3. **验证现有功能**
   - 启动服务: `python main.py`
   - 测试 API 接口
   - 检查日志输出

### 无需做的步骤

❌ **不需要修改现有代码**
- 所有使用 `BaseLLMClient` 的代码都无需修改
- API 接口保持不变
- 配置文件无需更改

❌ **不需要学习新的 API**
- 原有 API 完全兼容
- 可以继续使用熟悉的方式调用

## 优势

### 相比直接使用 OpenAI SDK

| 特性 | OpenAI SDK | LangChain |
|------|-----------|-----------|
| 统一接口 | ❌ 各 provider 不同 | ✅ 统一抽象 |
| 异步支持 | ⚠️ 需要单独实现 | ✅ 原生支持 |
| 消息类型 | ❌ 仅字典 | ✅ 类型安全 |
| 工具调用 | ❌ 不支持 | ✅ 原生支持 |
| 链式调用 | ❌ 不支持 | ✅ 支持 |
| 记忆管理 | ❌ 不支持 | ✅ 支持 |
| 向量存储 | ❌ 不支持 | ✅ 集成 |

### 扩展性

使用 LangChain 后,可以轻松实现:

1. **RAG (检索增强生成)**
   ```python
   from langchain_community.vectorstores import Chroma
   from langchain_openai import OpenAIEmbeddings

   vectorstore = Chroma.from_texts(texts, OpenAIEmbeddings())
   ```

2. **智能体 (Agents)**
   ```python
   from langchain.agents import create_openai_functions_agent

   agent = create_openai_functions_agent(llm, tools, prompt)
   ```

3. **工具调用 (Tools)**
   ```python
   from langchain.tools import Tool

   tool = Tool(
       name="calculator",
       func=lambda x: eval(x),
       description="计算表达式"
   )
   ```

## 性能优化

### 1. 缓存

LangChain 提供多种缓存策略:

```python
from langchain.cache import InMemoryCache, RedisCache
from langchain.globals import set_llm_cache

# 内存缓存
set_llm_cache(InMemoryCache())

# Redis 缓存
set_llm_cache(RedisCache(redis_client=redis))
```

### 2. 批量处理

使用批量接口减少调用次数:

```python
# 批量同步
responses = client.llm.batch(messages_list)

# 批量异步
responses = await client.llm.abatch(messages_list)
```

### 3. 并行调用

使用异步提高并发性能:

```python
tasks = [client.achat(msg) for msg in messages]
results = await asyncio.gather(*tasks)
```

## 测试覆盖

`test_langchain.py` 包含以下测试:

- ✅ 同步聊天
- ✅ 异步聊天
- ✅ 结构化数据提取
- ✅ JSON 提取
- ✅ 直接访问 LangChain LLM
- ✅ 批量异步调用
- ✅ 不同提供商
- ✅ 自定义参数

## 常见问题

### Q1: 为什么迁移到 LangChain?

A: LangChain 提供了:
- 统一的 LLM 抽象接口
- 丰富的生态系统
- 更好的可扩展性
- 原生异步支持
- 强大的链式调用能力

### Q2: 现有代码需要修改吗?

A: 不需要。所有使用 `BaseLLMClient` 的代码都完全兼容。

### Q3: 性能会受影响吗?

A: 不会。LangChain 的性能与直接使用 SDK 相当,而且提供了更多优化选项。

### Q4: 可以继续使用原有 API 吗?

A: 完全可以。原有 API 保持不变,可以无缝切换。

### Q5: 如何使用新的异步功能?

A: 使用 `client.achat()` 方法即可,详见测试脚本。

## 未来计划

基于 LangChain 的能力,未来可以实现:

1. **RAG 系统**: 集成向量存储,实现检索增强生成
2. **智能体**: 构建多工具协作的智能体
3. **工具调用**: 支持函数调用和外部工具集成
4. **记忆管理**: 添加对话记忆和上下文管理
5. **流式输出**: 实现实时流式响应
6. **批处理优化**: 优化批量处理性能

## 文档

- [LangChain 迁移指南](./LangChain迁移指南.md) - 详细使用说明
- [LangChain 使用说明](./LangChain使用说明.md) - 快速开始
- [测试脚本](../test_langchain.py) - 功能测试
- [官方文档](https://python.langchain.com/) - LangChain 官方文档

## 总结

本次 LangChain 集成实现了:

✅ **向后兼容**: 所有现有代码无需修改
✅ **功能增强**: 新增异步、批量等高级功能
✅ **易于扩展**: 为未来的 RAG、智能体等功能奠定基础
✅ **性能优化**: 提供缓存、批处理等性能优化手段
✅ **文档完善**: 提供详细的使用指南和测试脚本

开发者可以继续使用熟悉的 API,同时享受 LangChain 带来的强大功能和扩展性。
