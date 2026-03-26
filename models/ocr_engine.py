"""
OCR引擎 - 使用PaddleOCR进行文字识别
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

from utils.logger import get_logger
from utils.exceptions import OCRError

logger = get_logger(__name__)


class OCREngine:
    """OCR引擎 - 使用PaddleOCR进行文档文字识别"""

    def __init__(
        self,
        use_angle_cls: bool = True,
        lang: str = "ch",  # 中英文混合
        use_gpu: bool = False,
        show_log: bool = False,
    ):
        """
        初始化OCR引擎

        Args:
            use_angle_cls: 是否使用方向分类器
            lang: 语言 (ch=中英文, en=英文)
            use_gpu: 是否使用GPU（参数保留，PaddleOCR 3.4.0 不支持）
            show_log: 是否显示日志（已废弃，PaddleOCR不支持此参数）
        """
        if PaddleOCR is None:
            raise OCRError("PaddleOCR未安装,请先安装: pip install paddleocr")

        # PaddleOCR 初始化 - 只保留支持的参数
        self.ocr = PaddleOCR(
            use_angle_cls=use_angle_cls,
            lang=lang,
            # 注意：use_gpu 和 show_log 参数在新版本中不支持
        )
        self.lang = lang
        logger.info(f"OCR引擎初始化完成 (语言: {lang}, GPU支持: {use_gpu})")

    def recognize(self, image_path: str) -> List[Dict[str, Any]]:
        """
        识别图片中的文字

        Args:
            image_path: 图片路径

        Returns:
            识别结果列表,每个元素包含:
            - text: 识别的文本
            - box: 文本框坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            - confidence: 置信度

        Raises:
            OCRError: OCR识别失败时抛出
        """
        try:
            logger.debug(f"开始OCR识别: {image_path}")

            # 执行OCR识别
            result = self.ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                logger.warning(f"OCR未识别到文字: {image_path}")
                return []

            # 格式化结果
            ocr_results = []
            for line in result[0]:
                box = line[0]
                text_info = line[1]
                text = text_info[0]
                confidence = text_info[1]

                ocr_results.append({
                    "text": text,
                    "box": [[int(p[0]), int(p[1])] for p in box],
                    "confidence": float(confidence),
                })

            logger.info(f"OCR识别完成,识别到 {len(ocr_results)} 个文本块")
            return ocr_results

        except Exception as e:
            logger.error(f"OCR识别失败: {e}", exc_info=True)
            raise OCRError(f"OCR识别失败: {str(e)}") from e

    def extract_text(self, image_path: str, min_confidence: float = 0.5) -> str:
        """
        提取图片中的纯文本

        Args:
            image_path: 图片路径
            min_confidence: 最小置信度阈值

        Returns:
            提取的文本内容(按行拼接)
        """
        ocr_results = self.recognize(image_path)

        # 按box的y坐标排序,保持文本顺序
        ocr_results.sort(key=lambda x: x["box"][0][1])

        # 过滤低置信度的文本
        filtered_results = [
            r for r in ocr_results if r["confidence"] >= min_confidence
        ]

        # 拼接文本
        text_lines = [r["text"] for r in filtered_results]
        full_text = "\n".join(text_lines)

        logger.info(f"提取文本完成,共 {len(text_lines)} 行")
        return full_text

    def extract_structured_text(
        self,
        image_path: str,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        提取结构化的OCR结果,包含文本、坐标、置信度等信息

        Args:
            image_path: 图片路径
            min_confidence: 最小置信度阈值

        Returns:
            结构化结果:
            - text: 完整文本
            - lines: 文本行列表
            - total_blocks: 总文本块数
            - avg_confidence: 平均置信度
        """
        ocr_results = self.recognize(image_path)

        # 按y坐标排序
        ocr_results.sort(key=lambda x: x["box"][0][1])

        # 过滤低置信度
        filtered_results = [
            r for r in ocr_results if r["confidence"] >= min_confidence
        ]

        if not filtered_results:
            return {
                "text": "",
                "lines": [],
                "total_blocks": 0,
                "avg_confidence": 0.0,
            }

        # 计算平均置信度
        avg_confidence = sum(r["confidence"] for r in filtered_results) / len(filtered_results)

        # 构建结果
        lines = []
        for r in filtered_results:
            lines.append({
                "text": r["text"],
                "confidence": r["confidence"],
                "box": r["box"],
            })

        full_text = "\n".join([r["text"] for r in filtered_results])

        return {
            "text": full_text,
            "lines": lines,
            "total_blocks": len(filtered_results),
            "avg_confidence": round(avg_confidence, 3),
        }

    def batch_extract(
        self,
        image_paths: List[str],
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        批量提取文本

        Args:
            image_paths: 图片路径列表
            min_confidence: 最小置信度阈值

        Returns:
            每个图片的结构化结果列表
        """
        results = []
        for idx, image_path in enumerate(image_paths):
            logger.info(f"处理进度: {idx+1}/{len(image_paths)}")
            try:
                result = self.extract_structured_text(image_path, min_confidence)
                result["image_path"] = image_path
                results.append(result)
            except OCRError as e:
                logger.error(f"处理失败: {image_path}, 错误: {e}")
                results.append({
                    "image_path": image_path,
                    "error": str(e),
                    "text": "",
                    "lines": [],
                    "total_blocks": 0,
                    "avg_confidence": 0.0,
                })

        logger.info(f"批量提取完成,成功 {len([r for r in results if 'error' not in r])}/{len(results_paths)}")
        return results
