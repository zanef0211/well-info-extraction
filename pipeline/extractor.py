"""
信息提取器 - 使用LLM从文档中提取结构化信息
"""
import logging
from typing import Dict, List, Any, Optional
import json

from models.llm_client import BaseLLMClient
from config.prompts import Prompts
from config.field_schemas import FIELD_SCHEMAS, DOCUMENT_TYPES
from utils.logger import get_logger
from utils.exceptions import ExtractionError

logger = get_logger(__name__)


class DocumentExtractor:
    """文档信息提取器"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        max_retries: int = 2,
    ):
        """
        初始化提取器

        Args:
            llm_client: LLM客户端
            max_retries: 最大重试次数
        """
        self.llm_client = llm_client
        self.max_retries = max_retries
        logger.info("信息提取器初始化完成")

    def extract(
        self,
        document_text: str,
        document_type: str,
        document_id: str,
        target_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        从文档中提取结构化信息

        Args:
            document_text: 文档文本内容
            document_type: 文档类型
            document_id: 文档ID
            target_fields: 目标字段列表(可选)

        Returns:
            提取的字段数据

        Raises:
            ExtractionError: 提取失败时抛出
        """
        # 确定目标字段
        if target_fields is None:
            target_fields = self._get_target_fields(document_type)

        # 构建字段Schema
        field_schemas = self._build_field_schemas(target_fields)

        # 构建提示词
        prompt = self._build_extraction_prompt(
            document_text=document_text,
            document_type=document_type,
            field_schemas=field_schemas,
        )

        # 调用LLM提取
        extracted_data = self._call_llm_with_retry(prompt)

        # 验证和清理结果
        cleaned_data = self._validate_and_clean(extracted_data, target_fields)

        logger.info(
            f"信息提取完成: {document_id}, "
            f"成功提取 {len([v for v in cleaned_data.values() if v])}/{len(target_fields)} 个字段"
        )

        return cleaned_data

    def _get_target_fields(self, document_type: str) -> List[str]:
        """获取文档类型的目标字段"""
        if document_type in DOCUMENT_TYPES:
            doc_info = DOCUMENT_TYPES[document_type]
            return doc_info.get("target_fields", list(FIELD_SCHEMAS.keys()))
        return list(FIELD_SCHEMAS.keys())

    def _build_field_schemas(self, target_fields: List[str]) -> Dict[str, Dict]:
        """构建字段Schema"""
        schemas = {}
        for field_id in target_fields:
            if field_id in FIELD_SCHEMAS:
                schema = FIELD_SCHEMAS[field_id]
                schemas[field_id] = {
                    "name": schema["name"],
                    "type": schema["type"],
                    "description": schema.get("description", ""),
                    "required": schema.get("required", False),
                }
        return schemas

    def _build_extraction_prompt(
        self,
        document_text: str,
        document_type: str,
        field_schemas: Dict[str, Dict],
    ) -> str:
        """构建提取提示词"""
        # 格式化字段Schema
        field_schema_str = json.dumps(field_schemas, ensure_ascii=False, indent=2)

        # JSON 格式示例（单独定义避免 f-string 冲突）
        json_format = """{
  "字段ID1": "提取的值1",
  "字段ID2": "提取的值2",
  ...
}"""

        # 构建提示词
        prompt = f"""你是一位专业的油气田文档信息提取专家。请从以下文档中提取结构化信息。

文档类型: {document_type}

需要提取的字段信息:
{field_schema_str}

文档内容:
{document_text[:8000]}

请按照以下JSON格式输出提取结果:
{json_format}

注意事项:
1. 严格按照上面的字段ID和类型提取信息
2. 如果某个字段在文档中找不到,请设置为null
3. 数值类型请输出数字,不要包含单位
4. 日期格式统一为YYYY-MM-DD
5. 只输出JSON,不要添加任何其他说明文字
6. 字段值要尽量准确,如果不确定可以不填

现在开始提取:
"""

        return prompt

    def _call_llm_with_retry(self, prompt: str) -> Dict[str, Any]:
        """带重试的LLM调用"""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"LLM提取尝试 {attempt + 1}/{self.max_retries + 1}")

                messages = [
                    {"role": "user", "content": prompt}
                ]

                response = self.llm_client.chat(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000,
                )

                # 提取JSON
                result = self.llm_client.extract_json(response)

                logger.info(f"LLM提取成功 (尝试 {attempt + 1})")
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"LLM提取失败 (尝试 {attempt + 1}): {e}")

                if attempt < self.max_retries:
                    # 稍微提高温度以增加多样性
                    continue

        logger.error(f"LLM提取最终失败: {last_error}")
        raise ExtractionError(f"LLM提取失败: {str(last_error)}") from last_error

    def _validate_and_clean(
        self,
        extracted_data: Dict[str, Any],
        target_fields: List[str],
    ) -> Dict[str, Any]:
        """验证和清理提取结果"""
        cleaned = {}

        for field_id in target_fields:
            value = extracted_data.get(field_id)

            # 清理空值
            if value is None or value == "" or str(value).strip().lower() in ("null", "none", "n/a"):
                cleaned[field_id] = None
                continue

            # 根据字段类型进行清理
            if field_id in FIELD_SCHEMAS:
                field_type = FIELD_SCHEMAS[field_id]["type"]

                try:
                    if field_type == "number":
                        # 提取数字
                        import re
                        numbers = re.findall(r"[-+]?\d*\.?\d+", str(value))
                        if numbers:
                            cleaned[field_id] = float(numbers[0])
                        else:
                            cleaned[field_id] = None
                    elif field_type == "date":
                        # 统一日期格式
                        cleaned[field_id] = self._normalize_date(value)
                    elif field_type == "string":
                        cleaned[field_id] = str(value).strip()
                    else:
                        cleaned[field_id] = value
                except Exception as e:
                    logger.warning(f"字段清理失败 {field_id}: {e}")
                    cleaned[field_id] = None
            else:
                cleaned[field_id] = value

        return cleaned

    def _normalize_date(self, date_value: Any) -> Optional[str]:
        """规范化日期格式"""
        if not date_value:
            return None

        from datetime import datetime

        date_str = str(date_value).strip()

        # 尝试多种格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%Y.%m.%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # 如果已经是YYYY-MM-DD格式,直接返回
        if "-" in date_str and len(date_str.split("-")) == 3:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                pass

        logger.warning(f"无法规范化日期: {date_value}")
        return date_str

    def extract_batch(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        批量提取信息

        Args:
            documents: 文档列表,每个文档包含id, text, type等

        Returns:
            提取结果列表
        """
        results = []

        for idx, doc in enumerate(documents):
            logger.info(f"提取进度: {idx + 1}/{len(documents)}")
            try:
                data = self.extract(
                    document_text=doc["text"],
                    document_type=doc.get("type", "daily"),
                    document_id=doc.get("id", f"doc_{idx}"),
                    target_fields=doc.get("target_fields"),
                )
                results.append({
                    "document_id": doc.get("id", f"doc_{idx}"),
                    "data": data,
                    "success": True,
                })
            except ExtractionError as e:
                logger.error(f"提取失败: {doc.get('id', f'doc_{idx}')}, {e}")
                results.append({
                    "document_id": doc.get("id", f"doc_{idx}"),
                    "data": {},
                    "success": False,
                    "error": str(e),
                })

        success_count = sum(1 for r in results if r["success"])
        logger.info(f"批量提取完成,成功 {success_count}/{len(documents)}")

        return results
