"""
文档分类器 - 使用LLM进行零样本分类（支持二级分类）
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .llm_client import BaseLLMClient
from config.field_schemas import FieldSchemas
from utils.logger import get_logger
from utils.exceptions import ClassificationError

logger = get_logger(__name__)


@dataclass
class ClassificationResult:
    """分类结果（支持二级分类）"""
    category: str              # 一级分类代码: drilling/mudlogging等
    doc_category: str         # 二级文档分类: 钻井设计/完井设计等
    confidence: float         # 置信度
    reason: str              # 分类依据
    suggested_fields: List[str]  # 建议提取的字段


class DocumentClassifier:
    """基于LLM的文档分类器（支持二级分类）"""

    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化分类器

        Args:
            llm_client: LLM客户端
        """
        self.llm_client = llm_client
        # 获取一级分类和二级分类配置
        self.category_map = FieldSchemas.CATEGORY_MAP
        self.doc_categories = FieldSchemas.DOC_CATEGORIES
        logger.info("文档分类器初始化完成（支持二级分类）")

    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化分类器

        Args:
            llm_client: LLM客户端
        """
        self.llm_client = llm_client
        logger.info("文档分类器初始化完成")

    def classify(
        self,
        document_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> ClassificationResult:
        """
        对文档进行分类（支持二级分类）

        Args:
            document_text: 文档文本内容
            metadata: 文档元数据(文件名、创建日期等)
            top_k: 返回前k个可能的分类

        Returns:
            分类结果,包含一级分类、二级分类、置信度等

        Raises:
            ClassificationError: 分类失败时抛出
        """
        try:
            # 构建分类提示
            prompt = self._build_classification_prompt(document_text, metadata)

            # 构建二级分类说明
            doc_category_desc = self._build_doc_category_description()

            messages = [
                {
                    "role": "system",
                    "content": f"""你是一位专业的油气井文档分类专家。请根据文档内容准确判断文档的一级分类和二级分类。

{doc_category_desc}

输出JSON格式:
{{
  "category": "一级分类代码",
  "doc_category": "二级文档分类",
  "confidence": 0.95,
  "reason": "分类依据简述"
}}

请只输出JSON,不要有其他内容。"""
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ]

            # 调用LLM
            response = self.llm_client.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=500,
            )

            # 提取JSON结果
            result_dict = self.llm_client.extract_json(response)

            # 创建分类结果对象
            result = ClassificationResult(
                category=result_dict.get("category", "drilling"),
                doc_category=result_dict.get("doc_category", "其他"),
                confidence=float(result_dict.get("confidence", 0.5)),
                reason=result_dict.get("reason", ""),
                suggested_fields=[],
            )

            # 验证一级分类
            if result.category not in self.category_map:
                logger.warning(f"未知的一级分类: {result.category}, 使用默认值 drilling")
                result.category = "drilling"

            # 验证二级分类
            if result.category in self.doc_categories:
                valid_categories = self.doc_categories[result.category]
                if result.doc_category not in valid_categories:
                    logger.warning(
                        f"二级分类 {result.doc_category} 不属于一级分类 {result.category}, "
                        f"使用该分类的第一个选项: {valid_categories[0]}"
                    )
                    result.doc_category = valid_categories[0]

            # 根据分类获取建议提取的字段
            result.suggested_fields = self._get_suggested_fields(result.category)

            logger.info(
                f"文档分类完成: 一级分类={self.category_map[result.category]}, "
                f"二级分类={result.doc_category}, 置信度={result.confidence:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"文档分类失败: {e}", exc_info=True)
            raise ClassificationError(f"文档分类失败: {str(e)}") from e

    def _build_classification_prompt(
        self,
        document_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建分类提示词

        Args:
            document_text: 文档文本
            metadata: 元数据

        Returns:
            提示词
        """
        prompt_parts = []

        # 添加元数据
        if metadata:
            filename = metadata.get("filename", "")
            if filename:
                prompt_parts.append(f"文件名: {filename}\n")

            created_date = metadata.get("created_date", "")
            if created_date:
                prompt_parts.append(f"创建日期: {created_date}\n")

        # 添加文档内容(截取前3000字符)
        max_preview = 3000
        preview = document_text[:max_preview]
        if len(document_text) > max_preview:
            preview += "\n... (文档已截断)"

        prompt_parts.append(f"\n文档内容预览:\n{preview}")

        return "".join(prompt_parts)

    def classify_batch(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[ClassificationResult]:
        """
        批量分类文档

        Args:
            documents: 文档列表,每个文档包含text和可选的metadata

        Returns:
            分类结果列表
        """
        results = []

        for idx, doc in enumerate(documents):
            logger.info(f"分类进度: {idx+1}/{len(documents)}")
            try:
                result = self.classify(
                    document_text=doc["text"],
                    metadata=doc.get("metadata"),
                )
                results.append(result)
            except ClassificationError as e:
                logger.error(f"文档分类失败: {doc.get('metadata', {}).get('filename', f'文档{idx}')}")
                # 返回默认分类
                results.append(ClassificationResult(
                    category="drilling",
                    doc_category="其他",
                    confidence=0.0,
                    reason=f"分类失败: {str(e)}",
                    suggested_fields=[],
                ))

        success_count = len([r for r in results if r.confidence > 0])
        logger.info(f"批量分类完成,成功 {success_count}/{len(documents)}")
        return results

    def _build_doc_category_description(self) -> str:
        """构建二级分类描述"""
        description = "一级分类和二级文档分类:\n\n"
        for category_code, category_name in self.category_map.items():
            description += f"{category_name} ({category_code}):\n"
            if category_code in self.doc_categories:
                for doc_type in self.doc_categories[category_code]:
                    description += f"  - {doc_type}\n"
            description += "\n"
        return description

    def _get_suggested_fields(self, category: str) -> List[str]:
        """根据分类获取建议提取的字段"""
        try:
            fields = FieldSchemas.get_all_fields(category)
            return [f.name for f in fields if f.required or f.weight >= 1.0]
        except Exception:
            return []

    def get_target_fields(self, category: str) -> List[Dict[str, Any]]:
        """
        根据分类获取目标字段

        Args:
            category: 一级分类代码

        Returns:
            字段列表
        """
        try:
            fields = FieldSchemas.get_all_fields(category)
            return [
                {
                    "name": f.name,
                    "display_name": f.display_name,
                    "data_type": f.data_type,
                    "required": f.required,
                    "unit": f.unit,
                }
                for f in fields
            ]
        except Exception:
            return []
