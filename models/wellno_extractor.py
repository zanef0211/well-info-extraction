"""
井号识别器 - 从文档中识别和提取井号
"""
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .llm_client import BaseLLMClient
from utils.logger import get_logger
from utils.exceptions import ExtractionError

logger = get_logger(__name__)


@dataclass
class WellNoResult:
    """井号识别结果"""
    primary_well: str           # 主要井号 (归一化后)
    all_wells: List[str]        # 所有识别到的井号 (归一化后)
    raw_matches: List[Dict]     # 原始匹配信息
    confidence: float          # 识别置信度
    source: str                # 识别来源 (filename, content, or both)


class WellNoExtractor:
    """井号识别器 - 使用规则和LLM混合策略"""

    # 常见井号格式模式
    PATTERNS = [
        # 格式1: XX-1-1 (字母-数字-数字)
        r'[A-Z\u4e00-\u9fa5]+[-–]\d+[-–]\d+',
        # 格式2: XX1-1 (字母数字-数字)
        r'[A-Z\u4e00-\u9fa5]+\d+[-–]\d+',
        # 格式3: 试1-1, 探1-1 (汉字-数字-数字)
        r'[试探][一二三四五六七八九十百千万]+[-–]\d+',
        # 格式4: XX井 (字母+井)
        r'[A-Z\u4e00-\u9fa5]+\d*井',
        # 格式5: XX#1 (字母#数字)
        r'[A-Z\u4e00-\u9fa5]+#\d+',
        # 格式6: 井号:XX
        r'井号[:：]\s*[A-Z\u4e00-\u9fa5\d\-#]+',
    ]

    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化井号识别器

        Args:
            llm_client: LLM客户端
        """
        self.llm_client = llm_client
        self._compile_patterns()
        logger.info("井号识别器初始化完成")

    def _compile_patterns(self):
        """编译正则表达式"""
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATTERNS]

    def extract(
        self,
        filename: str,
        content: str,
        use_llm: bool = True,
        min_confidence: float = 0.6,
    ) -> WellNoResult:
        """
        从文档中提取井号

        Args:
            filename: 文件名
            content: 文档内容
            use_llm: 是否使用LLM确认
            min_confidence: 最低置信度阈值

        Returns:
            井号识别结果

        Raises:
            ExtractionError: 识别失败时抛出
        """
        logger.info(f"开始识别井号: filename={filename}")

        # 1. 从文件名提取 (优先级最高)
        filename_matches = self._extract_from_filename(filename)

        # 2. 从内容中提取
        content_matches = self._extract_from_content(content)

        # 3. 合并所有匹配
        all_matches = filename_matches + content_matches

        if not all_matches:
            logger.warning(f"未识别到井号: {filename}")
            return WellNoResult(
                primary_well="",
                all_wells=[],
                raw_matches=[],
                confidence=0.0,
                source="none"
            )

        # 4. 归一化井号
        normalized_wells = []
        for match in all_matches:
            normalized = self.normalize_well_no(match['text'])
            if normalized and normalized not in normalized_wells:
                normalized_wells.append(normalized)

        # 5. 确定主要井号
        primary_well = self._determine_primary_well(
            normalized_wells,
            filename_matches,
            content_matches
        )

        # 6. 计算置信度
        confidence = self._calculate_confidence(
            primary_well,
            all_matches,
            filename_matches
        )

        # 7. 如果需要且置信度不足,使用LLM确认
        if use_llm and confidence < 0.8 and len(normalized_wells) <= 5:
            logger.info(f"使用LLM确认井号: {filename}")
            primary_well = self._confirm_with_llm(
                filename,
                content,
                normalized_wells,
                primary_well
            )
            confidence = 0.95  # LLM确认后给高置信度

        result = WellNoResult(
            primary_well=primary_well,
            all_wells=normalized_wells,
            raw_matches=all_matches,
            confidence=confidence,
            source="llm" if use_llm and confidence > 0.9 else "rule"
        )

        logger.info(
            f"井号识别完成: {filename}, "
            f"主要井号={primary_well}, "
            f"置信度={confidence:.2f}, "
            f"识别到{len(normalized_wells)}个井号"
        )

        return result

    def _extract_from_filename(self, filename: str) -> List[Dict]:
        """从文件名提取井号"""
        matches = []
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(filename):
                matches.append({
                    'text': match.group(),
                    'source': 'filename',
                    'start': match.start(),
                    'end': match.end(),
                })
        return matches

    def _extract_from_content(self, content: str) -> List[Dict]:
        """从内容中提取井号"""
        # 只检查前2000字符 (通常井号出现在前面)
        preview = content[:2000]
        matches = []
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(preview):
                text = match.group()
                # 排除明显的误匹配 (如 "井段" 而不是井号)
                if self._is_valid_well_no(text):
                    matches.append({
                        'text': text,
                        'source': 'content',
                        'start': match.start(),
                        'end': match.end(),
                    })
        return matches

    def _is_valid_well_no(self, text: str) -> bool:
        """判断是否为有效的井号"""
        # 排除常见的误匹配
        invalid_patterns = [
            r'井段',  # 井段
            r'井距',  # 井距
            r'井网',  # 井网
            r'钻井',  # 钻井
            r'完井',  # 完井
            r'测试井',  # 测试井
        ]
        for invalid in invalid_patterns:
            if invalid in text:
                return False
        return True

    def _determine_primary_well(
        self,
        normalized_wells: List[str],
        filename_matches: List[Dict],
        content_matches: List[Dict]
    ) -> str:
        """确定主要井号"""
        if not normalized_wells:
            return ""

        # 优先选择文件名中的井号
        if filename_matches:
            for match in filename_matches:
                normalized = self.normalize_well_no(match['text'])
                if normalized in normalized_wells:
                    return normalized

        # 其次选择内容中最频繁出现的井号
        from collections import Counter
        well_counts = Counter(normalized_wells)
        return well_counts.most_common(1)[0][0]

    def _calculate_confidence(
        self,
        primary_well: str,
        all_matches: List[Dict],
        filename_matches: List[Dict]
    ) -> float:
        """计算识别置信度"""
        if not primary_well:
            return 0.0

        confidence = 0.6  # 基础置信度

        # 文件名中找到,增加置信度
        if any(self.normalize_well_no(m['text']) == primary_well
               for m in filename_matches):
            confidence += 0.3

        # 匹配数多,增加置信度
        if len(all_matches) >= 3:
            confidence += 0.1
        elif len(all_matches) >= 2:
            confidence += 0.05

        # 检查格式规范性
        if self._is_standard_format(primary_well):
            confidence += 0.05

        return min(confidence, 1.0)

    def _is_standard_format(self, well_no: str) -> bool:
        """检查是否为标准格式"""
        # 标准格式: 字母-数字-数字
        pattern = r'^[A-Z\u4e00-\u9fa5]+[-–]\d+[-–]\d+$'
        return bool(re.match(pattern, well_no.upper()))

    def _confirm_with_llm(
        self,
        filename: str,
        content: str,
        candidate_wells: List[str],
        current_primary: str,
    ) -> str:
        """使用LLM确认主要井号"""
        content_preview = content[:1000]

        prompt = f"""请分析以下文档,确定主要井号。

文件名: {filename}

文档内容预览:
{content_preview}

候选井号:
{', '.join(candidate_wells)}

当前识别的主要井号: {current_primary}

请判断:
1. 这些候选井号中哪个是该文档的主要井号?
2. 如果都不是,请识别出真正的主要井号
3. 如果没有井号,返回 "无"

请只返回主要井号,不要其他内容。"""

        try:
            response = self.llm_client.chat([
                {"role": "user", "content": prompt}
            ])

            # 清理响应
            result = response.strip()
            if result == "无" or not result:
                return current_primary

            # 归一化
            normalized = self.normalize_well_no(result)
            if normalized:
                return normalized

            return current_primary

        except Exception as e:
            logger.error(f"LLM确认井号失败: {e}, 使用规则识别结果")
            return current_primary

    def normalize_well_no(self, well_no: str) -> str:
        """
        归一化井号

        规则:
        1. 转为大写
        2. 统一使用短横线 "-"
        3. 去除多余空格
        4. 去除"井"字后缀
        """
        if not well_no:
            return ""

        # 大写
        normalized = well_no.upper()

        # 统一使用 "-"
        normalized = re.sub(r'[–—]', '-', normalized)

        # 去除空格
        normalized = re.sub(r'\s+', '', normalized)

        # 去除"井"字后缀
        normalized = re.sub(r'井$', '', normalized)

        # 去除"井号:"前缀
        normalized = re.sub(r'^井号[:：]', '', normalized)

        # 去除特殊字符(保留字母、数字、短横线、#)
        normalized = re.sub(r'[^A-Z0-9\-#]', '', normalized)

        return normalized

    def deduplicate_and_group(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按井号去重并分组

        Args:
            documents: 文档列表,每个文档应包含 well_no_result 字段

        Returns:
            按井号分组的文档字典 {normalized_well_no: [doc1, doc2, ...]}
        """
        well_groups = {}

        for doc in documents:
            well_result = doc.get('well_no_result')
            if not well_result or not well_result.primary_well:
                # 没有井号,放到"未识别"组
                if "未识别" not in well_groups:
                    well_groups["未识别"] = []
                well_groups["未识别"].append(doc)
                continue

            # 获取归一化的井号
            normalized_well = well_result.primary_well

            # 分组
            if normalized_well not in well_groups:
                well_groups[normalized_well] = []
            well_groups[normalized_well].append(doc)

        logger.info(
            f"文档分组完成: 总文档数={len(documents)}, "
            f"识别到井号={len(well_groups)-1 if '未识别' in well_groups else len(well_groups)}, "
            f"未识别={len(well_groups.get('未识别', []))}"
        )

        return well_groups

    def get_unique_wells(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        获取唯一井号列表

        Args:
            documents: 文档列表

        Returns:
            唯一井号列表(排序后)
        """
        well_set = set()

        for doc in documents:
            well_result = doc.get('well_no_result')
            if well_result and well_result.primary_well:
                well_set.add(well_result.primary_well)

        return sorted(list(well_set))

    def batch_extract(
        self,
        file_list: List[tuple]  # [(filename, content), ...]
    ) -> List[WellNoResult]:
        """
        批量提取井号

        Args:
            file_list: 文件列表,每个元素是 (filename, content) 元组

        Returns:
            井号识别结果列表
        """
        results = []

        for filename, content in file_list:
            try:
                result = self.extract(filename, content)
                results.append(result)
            except Exception as e:
                logger.error(f"提取井号失败: {filename}, {e}")
                # 返回空结果
                results.append(WellNoResult(
                    primary_well="",
                    all_wells=[],
                    raw_matches=[],
                    confidence=0.0,
                    source="error"
                ))

        return results
