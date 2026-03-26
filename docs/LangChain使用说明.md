# LangChain 集成说明

## 快速开始

### 1. 安装依赖

```bash
pip install langchain==0.1.0
pip install langchain-core==0.1.10
pip install langchain-openai==0.0.2
```

或更新 `requirements.txt`:

```txt
langchain==0.1.0
langchain-core==0.1.10
langchain-openai==0.0.2
```

**注意**: `langchain-openai` 会自动安装 `openai` 作为传递依赖,无需单独指定。

### 2. 基本使用

```python
from models.llm_client import LLMClientFactory

# 创建客户端
client = LLMClientFactory.create_client(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4o"
)

# 同步调用
response = client.chat([
    {"role": "user", "content": "你好"}
])
print(response)

# 异步调用
import asyncio
response = await client.achat([
    {"role": "user", "content": "你好"}
])
```

## 主要特性

✅ **向后兼容**: 所有现有代码无需修改
✅ **异步支持**: 新增 `achat()` 方法支持异步调用
✅ **直接访问**: 可直接访问 LangChain LLM 对象
✅ **多提供商支持**: OpenAI、DeepSeek、Qwen
✅ **结构化提取**: 内置 JSON 提取和结构化数据提取

## 兼容性说明

| 组件 | 状态 |
|------|------|
| `api/app.py` | ✅ 完全兼容 |
| `pipeline/processor.py` | ✅ 完全兼容 |
| `pipeline/extractor.py` | ✅ 完全兼容 |

所有使用 `BaseLLMClient` 的组件都无需修改。

## 测试

运行测试脚本:

```bash
python test_langchain.py
```

## 文档

- [详细迁移指南](./LangChain迁移指南.md) - 完整的使用说明和示例
- [官方文档](https://python.langchain.com/) - LangChain 官方文档
