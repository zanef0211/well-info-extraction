"""
文本文件解析器 - 解析TXT文件
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logger import get_logger
from utils.exceptions import ParsingError

logger = get_logger(__name__)


class TxtParser:
    """文本文件解析器 - 解析纯文本文件"""

    # 支持的文本编码
    ENCODINGS = ["utf-8", "gbk", "gb2312", "big5", "utf-16"]

    def __init__(self, default_encoding: str = "utf-8"):
        """
        初始化文本解析器

        Args:
            default_encoding: 默认文本编码
        """
        self.default_encoding = default_encoding
        logger.info(f"文本文件解析器初始化完成 (默认编码: {default_encoding})")

    def extract_text(
        self,
        txt_path: str,
        encoding: Optional[str] = None,
    ) -> str:
        """
        提取文本文件内容

        Args:
            txt_path: 文本文件路径
            encoding: 文本编码(可选,默认自动检测)

        Returns:
            文本内容

        Raises:
            ParsingError: 解析失败时抛出
        """
        try:
            logger.info(f"开始提取文本文件: {txt_path}")

            # 尝试读取文件
            text = self._read_with_encoding(txt_path, encoding)

            logger.info(f"文本文件提取完成,长度: {len(text)} 字符")
            return text

        except Exception as e:
            logger.error(f"文本文件提取失败: {e}", exc_info=True)
            raise ParsingError(f"文本文件提取失败: {str(e)}") from e

    def _read_with_encoding(
        self,
        txt_path: str,
        encoding: Optional[str] = None,
    ) -> str:
        """
        尝试用不同编码读取文件

        Args:
            txt_path: 文本文件路径
            encoding: 指定编码(可选)

        Returns:
            文本内容

        Raises:
            ParsingError: 所有编码都失败时抛出
        """
        if encoding:
            # 使用指定编码
            try:
                with open(txt_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError as e:
                raise ParsingError(f"编码 {encoding} 解码失败: {str(e)}") from e

        # 尝试不同编码
        encodings_to_try = [self.default_encoding] + self.ENCODINGS
        last_error = None

        for enc in encodings_to_try:
            try:
                with open(txt_path, "r", encoding=enc) as f:
                    text = f.read()
                    logger.debug(f"成功使用编码 {enc} 读取文件")
                    return text
            except UnicodeDecodeError as e:
                last_error = e
                logger.debug(f"编码 {enc} 失败: {e}")
                continue

        # 所有编码都失败
        raise ParsingError(
            f"无法使用任何编码读取文件,尝试的编码: {encodings_to_try}"
        ) from last_error

    def extract_lines(
        self,
        txt_path: str,
        skip_empty: bool = True,
        max_lines: Optional[int] = None,
    ) -> List[str]:
        """
        按行提取文本

        Args:
            txt_path: 文本文件路径
            skip_empty: 是否跳过空行
            max_lines: 最大行数(可选)

        Returns:
            文本行列表
        """
        try:
            text = self.extract_text(txt_path)
            lines = text.split("\n")

            if skip_empty:
                lines = [line.strip() for line in lines if line.strip()]

            if max_lines:
                lines = lines[:max_lines]

            logger.info(f"按行提取完成,共 {len(lines)} 行")
            return lines

        except Exception as e:
            logger.error(f"按行提取失败: {e}", exc_info=True)
            raise ParsingError(f"按行提取失败: {str(e)}") from e

    def extract_paragraphs(
        self,
        txt_path: str,
        min_length: int = 10,
    ) -> List[str]:
        """
        提取段落(按空行分隔)

        Args:
            txt_path: 文本文件路径
            min_length: 最小段落长度

        Returns:
            段落列表
        """
        try:
            text = self.extract_text(txt_path)

            # 按空行分割段落
            paragraphs = []
            current_para = []

            for line in text.split("\n"):
                line = line.strip()
                if line:
                    current_para.append(line)
                elif current_para:
                    # 空行,保存当前段落
                    para_text = " ".join(current_para)
                    if len(para_text) >= min_length:
                        paragraphs.append(para_text)
                    current_para = []

            # 保存最后一个段落
            if current_para:
                para_text = " ".join(current_para)
                if len(para_text) >= min_length:
                    paragraphs.append(para_text)

            logger.info(f"段落提取完成,共 {len(paragraphs)} 个段落")
            return paragraphs

        except Exception as e:
            logger.error(f"段落提取失败: {e}", exc_info=True)
            raise ParsingError(f"段落提取失败: {str(e)}") from e

    def get_file_info(self, txt_path: str) -> Dict[str, Any]:
        """
        获取文本文件信息

        Args:
            txt_path: 文本文件路径

        Returns:
            文件信息字典
        """
        try:
            text = self.extract_text(txt_path)
            path_obj = Path(txt_path)

            lines = text.split("\n")
            non_empty_lines = [line for line in lines if line.strip()]
            paragraphs = text.split("\n\n")

            # 尝试检测编码
            detected_encoding = self.default_encoding
            for enc in self.ENCODINGS:
                try:
                    with open(txt_path, "r", encoding=enc) as f:
                        f.read()
                        detected_encoding = enc
                        break
                except UnicodeDecodeError:
                    continue

            return {
                "file_path": txt_path,
                "file_name": path_obj.name,
                "file_size": path_obj.stat().st_size,
                "file_size_mb": round(path_obj.stat().st_size / (1024 * 1024), 2),
                "total_lines": len(lines),
                "non_empty_lines": len(non_empty_lines),
                "paragraphs": len(paragraphs),
                "character_count": len(text),
                "word_count": len(text.split()),
                "encoding": detected_encoding,
            }

        except Exception as e:
            logger.error(f"获取文本文件信息失败: {e}", exc_info=True)
            raise ParsingError(f"获取文本文件信息失败: {str(e)}") from e

    def search_text(
        self,
        txt_path: str,
        keyword: str,
        case_sensitive: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        在文本中搜索关键词

        Args:
            txt_path: 文本文件路径
            keyword: 关键词
            case_sensitive: 是否区分大小写

        Returns:
            匹配结果列表
        """
        try:
            text = self.extract_text(txt_path)

            if not case_sensitive:
                search_text = text.lower()
                keyword = keyword.lower()
            else:
                search_text = text

            matches = []
            start_idx = 0

            while True:
                idx = search_text.find(keyword, start_idx)
                if idx == -1:
                    break

                # 获取上下文
                context_start = max(0, idx - 50)
                context_end = min(len(text), idx + len(keyword) + 50)
                context = text[context_start:context_end]

                # 计算行号
                line_start = text.rfind("\n", 0, idx) + 1
                line_end = text.find("\n", idx)
                if line_end == -1:
                    line_end = len(text)
                line_number = text[:line_start].count("\n") + 1
                line_text = text[line_start:line_end]

                matches.append({
                    "index": idx,
                    "line_number": line_number,
                    "line_text": line_text.strip(),
                    "context": context,
                })

                start_idx = idx + 1

            logger.info(f"关键词搜索完成: {keyword}, 匹配数: {len(matches)}")
            return matches

        except Exception as e:
            logger.error(f"关键词搜索失败: {e}", exc_info=True)
            raise ParsingError(f"关键词搜索失败: {str(e)}") from e
