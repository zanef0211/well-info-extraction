"""
PDF解析器 - 提取PDF中的文本和图像
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import io

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
except ImportError:
    Image = None

from utils.logger import get_logger
from utils.exceptions import ParsingError

logger = get_logger(__name__)


class PDFParser:
    """PDF解析器 - 使用PyMuPDF解析PDF文档"""

    def __init__(
        self,
        dpi: int = 300,
        extract_images: bool = True,
        image_format: str = "png",
    ):
        """
        初始化PDF解析器

        Args:
            dpi: 图像提取的DPI
            extract_images: 是否提取页面图像
            image_format: 图像格式 (png/jpeg)
        """
        if fitz is None:
            raise ParsingError("PyMuPDF未安装,请先安装: pip install pymupdf")

        self.dpi = dpi
        self.extract_images = extract_images
        self.image_format = image_format.lower()
        logger.info(f"PDF解析器初始化完成 (DPI: {dpi})")

    def extract_text(self, pdf_path: str) -> str:
        """
        提取PDF中的所有文本

        Args:
            pdf_path: PDF文件路径

        Returns:
            完整文本内容

        Raises:
            ParsingError: 解析失败时抛出
        """
        try:
            logger.info(f"开始提取文本: {pdf_path}")

            doc = fitz.open(pdf_path)
            all_text = []

            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    all_text.append(page_text)

            full_text = "\n\n".join(all_text)
            logger.info(f"文本提取完成,共 {len(doc)} 页")

            doc.close()
            return full_text

        except Exception as e:
            logger.error(f"PDF文本提取失败: {e}", exc_info=True)
            raise ParsingError(f"PDF文本提取失败: {str(e)}") from e

    def extract_text_by_page(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        按页提取PDF文本

        Args:
            pdf_path: PDF文件路径

        Returns:
            每页的文本信息列表
        """
        try:
            doc = fitz.open(pdf_path)
            pages_text = []

            for page_num, page in enumerate(doc):
                text = page.get_text()
                pages_text.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "text_length": len(text),
                })

            doc.close()
            logger.info(f"按页提取完成,共 {len(pages_text)} 页")
            return pages_text

        except Exception as e:
            logger.error(f"PDF按页提取失败: {e}", exc_info=True)
            raise ParsingError(f"PDF按页提取失败: {str(e)}") from e

    def extract_images(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        prefix: str = "page",
    ) -> List[str]:
        """
        将PDF页面转换为图像

        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录(默认为PDF同级目录)
            prefix: 文件名前缀

        Returns:
            生成的图像文件路径列表
        """
        if not self.extract_images:
            logger.warning("图像提取未启用")
            return []

        try:
            doc = fitz.open(pdf_path)
            pdf_path_obj = Path(pdf_path)

            # 确定输出目录
            if output_dir:
                output_dir = Path(output_dir)
            else:
                output_dir = pdf_path_obj.parent / f"{pdf_path_obj.stem}_images"

            output_dir.mkdir(parents=True, exist_ok=True)
            image_paths = []

            for page_num, page in enumerate(doc):
                # 渲染页面为图像
                mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                pix = page.get_pixmap(matrix=mat)

                # 生成文件名
                image_name = f"{prefix}_{page_num + 1:03d}.{self.image_format}"
                image_path = output_dir / image_name

                # 保存图像
                if self.image_format == "png":
                    pix.save(str(image_path))
                elif self.image_format == "jpeg":
                    pix.save(str(image_path), jpeg_quality=95)
                else:
                    # 默认PNG
                    pix.save(str(image_path))

                image_paths.append(str(image_path))
                logger.debug(f"页面 {page_num + 1} 已转换为图像: {image_path}")

            doc.close()
            logger.info(f"PDF转图像完成,共 {len(image_paths)} 页")
            return image_paths

        except Exception as e:
            logger.error(f"PDF图像提取失败: {e}", exc_info=True)
            raise ParsingError(f"PDF图像提取失败: {str(e)}") from e

    def get_page_count(self, pdf_path: str) -> int:
        """
        获取PDF页数

        Args:
            pdf_path: PDF文件路径

        Returns:
            页数
        """
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            logger.error(f"获取PDF页数失败: {e}")
            raise ParsingError(f"获取PDF页数失败: {str(e)}") from e

    def extract_page_image(
        self,
        pdf_path: str,
        page_num: int,
        output_path: Optional[str] = None,
    ) -> str:
        """
        提取单页图像

        Args:
            pdf_path: PDF文件路径
            page_num: 页码(从1开始)
            output_path: 输出路径(可选)

        Returns:
            图像文件路径
        """
        try:
            doc = fitz.open(pdf_path)

            if page_num < 1 or page_num > len(doc):
                raise ParsingError(f"页码超出范围: {page_num}, 总页数: {len(doc)}")

            page = doc[page_num - 1]  # 转换为0-based索引
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # 确定输出路径
            if output_path:
                image_path = output_path
            else:
                pdf_path_obj = Path(pdf_path)
                output_dir = pdf_path_obj.parent / f"{pdf_path_obj.stem}_images"
                output_dir.mkdir(parents=True, exist_ok=True)
                image_path = str(output_dir / f"page_{page_num:03d}.png")

            pix.save(image_path)
            doc.close()

            logger.info(f"单页图像提取完成: 页码 {page_num} -> {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"单页图像提取失败: {e}", exc_info=True)
            raise ParsingError(f"单页图像提取失败: {str(e)}") from e

    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        获取PDF信息

        Args:
            pdf_path: PDF文件路径

        Returns:
            PDF信息字典
        """
        try:
            doc = fitz.open(pdf_path)

            metadata = doc.metadata
            page_count = len(doc)

            info = {
                "page_count": page_count,
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "is_encrypted": doc.is_encrypted,
            }

            doc.close()
            return info

        except Exception as e:
            logger.error(f"获取PDF信息失败: {e}")
            raise ParsingError(f"获取PDF信息失败: {str(e)}") from e

    def extract_tables(
        self,
        pdf_path: str,
    ) -> List[Dict[str, Any]]:
        """
        提取PDF中的表格(简单版本)

        注意: PyMuPDF的表格检测能力有限,复杂表格建议使用pdfplumber

        Args:
            pdf_path: PDF文件路径

        Returns:
            表格列表
        """
        try:
            doc = fitz.open(pdf_path)
            tables = []

            for page_num, page in enumerate(doc):
                # 检测表格(简单版本)
                # 这里只做基本检测,实际应用可能需要更复杂的逻辑
                tabs = page.find_tables()
                if tabs.tables:
                    for idx, table in enumerate(tabs.tables):
                        tables.append({
                            "page_number": page_num + 1,
                            "table_number": idx + 1,
                            "rows": table.extract(),
                            "bbox": table.bbox,
                        })

            doc.close()
            logger.info(f"检测到 {len(tables)} 个表格")
            return tables

        except Exception as e:
            logger.error(f"表格提取失败: {e}", exc_info=True)
            raise ParsingError(f"表格提取失败: {str(e)}") from e
