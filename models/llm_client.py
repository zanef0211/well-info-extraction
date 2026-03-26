"""
大语言模型客户端 - 使用 LangChain
"""
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

try:
    from langchain_core.language_models import BaseChatModel
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
except ImportError:
    BaseChatModel = None
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None
    AIMessage = None

from utils.logger import get_logger
from utils.exceptions import LLMError

logger = get_logger(__name__)


class BaseLLMClient(ABC):
    """LLM客户端基类"""

    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """聊天接口"""
        pass

    @abstractmethod
    def extract_json(self, response: str) -> Dict:
        """从响应中提取JSON"""
        pass


class LangChainLLMClient(BaseLLMClient):
    """基于 LangChain 的 LLM 客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        temperature: float = 0.1,
        max_tokens: int = 4000,
        timeout: int = 60,
        streaming: bool = False,
    ):
        """
        初始化 LangChain LLM 客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            temperature: 温度参数(0-1)
            max_tokens: 最大token数
            timeout: 超时时间(秒)
            streaming: 是否启用流式输出
        """
        if BaseChatModel is None or ChatOpenAI is None:
            raise LLMError("langchain 库未安装,请先安装: pip install langchain langchain-openai")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.streaming = streaming

        try:
            self.llm = ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                streaming=streaming,
            )
            logger.info(f"LangChain LLM 客户端初始化成功,模型: {model}")
        except Exception as e:
            logger.error(f"LangChain LLM 客户端初始化失败: {e}", exc_info=True)
            raise LLMError(f"LangChain LLM 客户端初始化失败: {str(e)}") from e

    def _convert_messages(
        self,
        messages: List[Dict[str, str]]
    ) -> List:
        """
        将消息列表转换为 LangChain 消息格式

        Args:
            messages: 消息列表,每个消息包含role和content

        Returns:
            LangChain 消息列表
        """
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant" or role == "ai":
                langchain_messages.append(AIMessage(content=content))
            else:  # user 或其他
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        聊天接口

        Args:
            messages: 消息列表,每个消息包含role和content
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            模型响应文本

        Raises:
            LLMError: 调用失败时抛出
        """
        try:
            logger.debug(f"调用LLM,模型: {self.model}, 消息数: {len(messages)}")

            # 转换消息格式
            langchain_messages = self._convert_messages(messages)

            # 构建调用参数
            invoke_kwargs = {}
            if temperature is not None:
                invoke_kwargs["temperature"] = temperature
            if max_tokens is not None:
                invoke_kwargs["max_tokens"] = max_tokens
            invoke_kwargs.update(kwargs)

            # 调用 LLM
            response = self.llm.invoke(langchain_messages, **invoke_kwargs)
            content = response.content

            logger.debug(f"LLM响应完成")

            return content

        except Exception as e:
            logger.error(f"LLM调用失败: {e}", exc_info=True)
            raise LLMError(f"LLM调用失败: {str(e)}") from e

    async def achat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        异步聊天接口

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            模型响应文本
        """
        try:
            logger.debug(f"异步调用LLM,模型: {self.model}, 消息数: {len(messages)}")

            langchain_messages = self._convert_messages(messages)

            invoke_kwargs = {}
            if temperature is not None:
                invoke_kwargs["temperature"] = temperature
            if max_tokens is not None:
                invoke_kwargs["max_tokens"] = max_tokens
            invoke_kwargs.update(kwargs)

            response = await self.llm.ainvoke(langchain_messages, **invoke_kwargs)
            content = response.content

            logger.debug(f"LLM异步响应完成")

            return content

        except Exception as e:
            logger.error(f"LLM异步调用失败: {e}", exc_info=True)
            raise LLMError(f"LLM异步调用失败: {str(e)}") from e

    def extract_json(self, response: str) -> Dict:
        """
        从响应中提取JSON数据

        Args:
            response: LLM响应文本

        Returns:
            解析后的JSON字典

        Raises:
            LLMError: JSON解析失败时抛出
        """
        import json
        import re

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取```json...```块
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取```...```块
        code_pattern = r'```\s*(.*?)\s*```'
        match = re.search(code_pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试查找 {...}
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(brace_pattern, response)
        if matches:
            try:
                for json_str in matches[::-1]:
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass

        raise LLMError(f"无法从响应中提取有效的JSON: {response[:200]}...")

    def extract_structured(
        self,
        messages: List[Dict[str, str]],
        schema: Dict,
        **kwargs
    ) -> Dict:
        """
        提取结构化数据

        Args:
            messages: 消息列表
            schema: 输出Schema,用于提示模型按特定格式输出
            **kwargs: 其他参数

        Returns:
            结构化的JSON数据
        """
        # 添加格式说明到消息中
        import json
        format_msg = {
            "role": "system",
            "content": f"""请严格按照以下JSON格式输出结果:
{json.dumps(schema, ensure_ascii=False, indent=2)}

注意:
1. 必须输出有效的JSON格式
2. 只输出JSON,不要添加其他说明文字
3. 所有字段名必须与Schema一致
""",
        }
        messages = [format_msg] + messages

        response = self.chat(messages, **kwargs)
        return self.extract_json(response)


class OpenAIClient(LangChainLLMClient):
    """OpenAI 客户端(使用 LangChain)"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        **kwargs
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            **kwargs
        )


class DeepSeekClient(LangChainLLMClient):
    """DeepSeek LLM 客户端(使用 LangChain)"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        **kwargs
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            **kwargs
        )


class QwenClient(LangChainLLMClient):
    """Qwen LLM 客户端(使用 LangChain)"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-plus",
        **kwargs
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            **kwargs
        )


class LLMClientFactory:
    """LLM 客户端工厂"""

    @staticmethod
    def create_client(
        provider: str,
        api_key: str,
        **kwargs
    ) -> BaseLLMClient:
        """
        创建 LLM 客户端

        Args:
            provider: 提供商 (openai, deepseek, qwen)
            api_key: API 密钥
            **kwargs: 其他参数

        Returns:
            LLM 客户端实例

        Raises:
            LLMError: 不支持的提供商时抛出
        """
        provider = provider.lower()

        if provider == "openai":
            return OpenAIClient(api_key=api_key, **kwargs)
        elif provider == "deepseek":
            return DeepSeekClient(api_key=api_key, **kwargs)
        elif provider == "qwen":
            return QwenClient(api_key=api_key, **kwargs)
        else:
            raise LLMError(f"不支持的 LLM 提供商: {provider}")
