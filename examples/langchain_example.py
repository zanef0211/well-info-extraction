"""
LangChain LLM 客户端使用示例
"""
import os
import asyncio
from dotenv import load_dotenv

from models.llm_client import LLMClientFactory

# 加载环境变量
load_dotenv()


def example_1_basic_chat():
    """示例 1: 基础聊天"""
    print("=" * 60)
    print("示例 1: 基础聊天")
    print("=" * 60)

    # 创建客户端
    client = LLMClientFactory.create_client(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model="gpt-4o-mini"
    )

    # 聊天
    messages = [
        {"role": "system", "content": "你是一个专业的助手"},
        {"role": "user", "content": "请简单介绍一下 AI 驱动的油气井信息提取"}
    ]

    response = client.chat(messages)
    print(f"\n响应:\n{response}\n")


def example_2_structured_extraction():
    """示例 2: 结构化数据提取"""
    print("=" * 60)
    print("示例 2: 结构化数据提取")
    print("=" * 60)

    client = LLMClientFactory.create_client(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model="gpt-4o-mini",
        temperature=0.1
    )

    # 定义提取的 Schema
    schema = {
        "井号": "",
        "井深": 0,
        "井类型": "",
        "开钻日期": "",
        "完钻日期": ""
    }

    # 构建提示词
    messages = [
        {
            "role": "user",
            "content": """请从以下文本中提取井信息:

XX-1-1井是一口生产井,位于XX区块,于2023年1月15日开钻,
2023年3月20日完钻,完钻井深3000米,斜深3200米,垂深2800米,
井底位移800米。

请按照指定格式提取以上信息。"""
        }
    ]

    # 提取结构化数据
    result = client.extract_structured(messages, schema)
    print(f"\n提取结果:\n{result}\n")


def example_3_async_call():
    """示例 3: 异步调用"""
    print("=" * 60)
    print("示例 3: 异步调用")
    print("=" * 60)

    async def async_example():
        client = LLMClientFactory.create_client(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model="gpt-4o-mini"
        )

        messages = [
            {"role": "user", "content": "用一句话介绍你自己"}
        ]

        response = await client.achat(messages)
        print(f"\n响应:\n{response}\n")

    asyncio.run(async_example())


async def example_4_batch_processing():
    """示例 4: 批量异步处理"""
    print("=" * 60)
    print("示例 4: 批量异步处理")
    print("=" * 60)

    client = LLMClientFactory.create_client(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model="gpt-4o-mini",
        temperature=0.1
    )

    # 多个任务
    tasks = [
        client.achat([{"role": "user", "content": f"问题{i}: 介绍一下油气井的类型"}])
        for i in range(3)
    ]

    # 并行执行
    print("\n开始批量处理...")
    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results, 1):
        print(f"\n任务 {i}:\n{result[:100]}...")
    print()


def example_5_direct_langchain_access():
    """示例 5: 直接访问 LangChain LLM"""
    print("=" * 60)
    print("示例 5: 直接访问 LangChain LLM")
    print("=" * 60)

    client = LLMClientFactory.create_client(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model="gpt-4o-mini"
    )

    # 直接访问 LangChain LLM 对象
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = client.llm
    messages = [
        SystemMessage(content="你是一个专业的助手"),
        HumanMessage(content="你好,请介绍一下 LangChain")
    ]

    response = llm.invoke(messages)
    print(f"\n响应:\n{response.content}\n")


def example_6_different_providers():
    """示例 6: 使用不同的 LLM 提供商"""
    print("=" * 60)
    print("示例 6: 使用不同的 LLM 提供商")
    print("=" * 60)

    providers = [
        ("openai", "gpt-4o-mini", os.getenv("OPENAI_API_KEY")),
        ("deepseek", "deepseek-chat", os.getenv("DEEPSEEK_API_KEY")),
        ("qwen", "qwen-plus", os.getenv("QWEN_API_KEY"))
    ]

    for provider, model, api_key in providers:
        if not api_key:
            print(f"\n⚠️  {provider}: 未设置 API Key,跳过")
            continue

        try:
            client = LLMClientFactory.create_client(
                provider=provider,
                api_key=api_key,
                model=model
            )

            response = client.chat([
                {"role": "user", "content": "你好"}
            ])

            print(f"\n✅ {provider} ({model}):")
            print(f"   {response[:50]}...")
        except Exception as e:
            print(f"\n❌ {provider} ({model}): {e}")

    print()


def example_7_custom_parameters():
    """示例 7: 自定义参数"""
    print("=" * 60)
    print("示例 7: 自定义参数")
    print("=" * 60)

    client = LLMClientFactory.create_client(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=150
    )

    # 调用时覆盖参数
    response = client.chat(
        [
            {"role": "user", "content": "请用一句话介绍 Python"}
        ],
        temperature=0.3,  # 覆盖默认值
        max_tokens=50      # 覆盖默认值
    )

    print(f"\n响应:\n{response}\n")


def example_8_with_pipeline():
    """示例 8: 与处理管道集成"""
    print("=" * 60)
    print("示例 8: 与处理管道集成")
    print("=" * 60)

    from pipeline.pipeline import ProcessingPipeline
    from models.ocr_engine import OCREngine
    from config.settings import settings

    # 初始化组件
    ocr_engine = OCREngine(
        use_angle_cls=True,
        lang="ch",
        use_gpu=settings.OCR_USE_GPU
    )

    llm_client = LLMClientFactory.create_client(
        provider=settings.LLM_PROVIDER,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.1
    )

    # 创建处理管道
    pipeline = ProcessingPipeline(
        ocr_engine=ocr_engine,
        llm_client=llm_client,
        enhance_images=True,
        clean_text=True
    )

    print("\n✅ 处理管道初始化成功")
    print("\n提示: 可以使用 pipeline.process_file() 处理文档文件\n")


def run_examples():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("LangChain LLM 客户端使用示例")
    print("=" * 60 + "\n")

    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置 OPENAI_API_KEY 环境变量")
        print("请在 .env 文件中设置:")
        print("OPENAI_API_KEY=your-api-key\n")
        return

    try:
        # 示例 1: 基础聊天
        example_1_basic_chat()

        # 示例 2: 结构化数据提取
        example_2_structured_extraction()

        # 示例 3: 异步调用
        example_3_async_call()

        # 示例 4: 批量异步处理
        asyncio.run(example_4_batch_processing())

        # 示例 5: 直接访问 LangChain LLM
        example_5_direct_langchain_access()

        # 示例 6: 不同提供商
        example_6_different_providers()

        # 示例 7: 自定义参数
        example_7_custom_parameters()

        # 示例 8: 与处理管道集成
        example_8_with_pipeline()

        print("=" * 60)
        print("所有示例运行完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_examples()
