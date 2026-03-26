"""
图像处理器 - 处理图像预处理、增强
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import io

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    Image = None

from utils.logger import get_logger
from utils.exceptions import ImageError

logger = get_logger(__name__)


class ImageProcessor:
    """图像处理器 - 图像预处理和增强"""

    def __init__(
        self,
        dpi: int = 300,
        output_format: str = "PNG",
    ):
        """
        初始化图像处理器

        Args:
            dpi: 目标DPI
            output_format: 输出格式 (PNG/JPEG)
        """
        if Image is None:
            raise ImageError("Pillow未安装,请先安装: pip install Pillow")

        self.dpi = dpi
        self.output_format = output_format.upper()
        logger.info(f"图像处理器初始化完成 (DPI: {dpi}, 格式: {output_format})")

    def load_image(self, image_path: str) -> "Image.Image":
        """
        加载图像

        Args:
            image_path: 图像路径

        Returns:
            PIL Image对象

        Raises:
            ImageError: 加载失败时抛出
        """
        try:
            image = Image.open(image_path)
            logger.debug(f"图像加载成功: {image_path}, 尺寸: {image.size}")
            return image
        except Exception as e:
            logger.error(f"图像加载失败: {e}", exc_info=True)
            raise ImageError(f"图像加载失败: {str(e)}") from e

    def resize_image(
        self,
        image: "Image.Image",
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        maintain_aspect: bool = True,
    ) -> "Image.Image":
        """
        调整图像大小

        Args:
            image: PIL Image对象
            max_width: 最大宽度
            max_height: 最大高度
            maintain_aspect: 是否保持宽高比

        Returns:
            调整后的图像
        """
        if max_width is None and max_height is None:
            return image

        width, height = image.size

        if maintain_aspect:
            if max_width and width > max_width:
                ratio = max_width / width
                new_size = (max_width, int(height * ratio))
            elif max_height and height > max_height:
                ratio = max_height / height
                new_size = (int(width * ratio), max_height)
            else:
                return image
        else:
            new_width = max_width or width
            new_height = max_height or height
            new_size = (new_width, new_height)

        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        logger.debug(f"图像调整大小: {image.size} -> {new_size}")
        return resized

    def enhance_contrast(
        self,
        image: "Image.Image",
        factor: float = 1.5,
    ) -> "Image.Image":
        """
        增强对比度

        Args:
            image: PIL Image对象
            factor: 对比度因子(>1增强, <1减弱)

        Returns:
            增强后的图像
        """
        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(factor)
        logger.debug(f"对比度增强: factor={factor}")
        return enhanced

    def enhance_sharpness(
        self,
        image: "Image.Image",
        factor: float = 1.5,
    ) -> "Image.Image":
        """
        增强锐度

        Args:
            image: PIL Image对象
            factor: 锐度因子(>1锐化, <1模糊)

        Returns:
            增强后的图像
        """
        enhancer = ImageEnhance.Sharpness(image)
        enhanced = enhancer.enhance(factor)
        logger.debug(f"锐度增强: factor={factor}")
        return enhanced

    def enhance_brightness(
        self,
        image: "Image.Image",
        factor: float = 1.2,
    ) -> "Image.Image":
        """
        调整亮度

        Args:
            image: PIL Image对象
            factor: 亮度因子(>1变亮, <1变暗)

        Returns:
            调整后的图像
        """
        enhancer = ImageEnhance.Brightness(image)
        enhanced = enhancer.enhance(factor)
        logger.debug(f"亮度调整: factor={factor}")
        return enhanced

    def denoise(
        self,
        image: "Image.Image",
        radius: int = 1,
    ) -> "Image.Image":
        """
        去噪(使用高斯模糊)

        Args:
            image: PIL Image对象
            radius: 模糊半径

        Returns:
            去噪后的图像
        """
        denoised = image.filter(ImageFilter.GaussianBlur(radius=radius))
        logger.debug(f"图像去噪: radius={radius}")
        return denoised

    def binarize(
        self,
        image: "Image.Image",
        threshold: int = 128,
    ) -> "Image.Image":
        """
        二值化(转换为黑白图像)

        Args:
            image: PIL Image对象
            threshold: 二值化阈值(0-255)

        Returns:
            二值化图像
        """
        # 转换为灰度
        gray = image.convert("L")

        # 二值化
        binary = gray.point(lambda x: 255 if x > threshold else 0, mode="1")

        logger.debug(f"图像二值化: threshold={threshold}")
        return binary

    def auto_enhance(
        self,
        image: "Image.Image",
    ) -> "Image.Image":
        """
        自动增强图像(组合多个增强操作)

        Args:
            image: PIL Image对象

        Returns:
            增强后的图像
        """
        # 1. 调整对比度
        image = self.enhance_contrast(image, factor=1.3)

        # 2. 调整锐度
        image = self.enhance_sharpness(image, factor=1.5)

        # 3. 轻微去噪
        # image = self.denoise(image, radius=1)

        logger.debug("自动图像增强完成")
        return image

    def deskew(
        self,
        image: "Image.Image",
    ) -> "Image.Image":
        """
        纠正倾斜(简单版本)

        注意: 完整的纠斜需要更复杂的算法,这里使用简单的旋转

        Args:
            image: PIL Image对象

        Returns:
            纠正后的图像
        """
        # 这里只是占位,实际实现需要检测图像倾斜角度
        # 可以使用OpenCV或skimage进行精确的倾斜检测
        logger.debug("倾斜纠正(暂未实现)")
        return image

    def preprocess_for_ocr(
        self,
        image_path: str,
        enhance: bool = True,
        binary: bool = False,
        output_path: Optional[str] = None,
    ) -> str:
        """
        为OCR预处理图像

        Args:
            image_path: 图像路径
            enhance: 是否自动增强
            binary: 是否二值化
            output_path: 输出路径(默认在原路径后添加_processed)

        Returns:
            预处理后的图像路径
        """
        # 加载图像
        image = self.load_image(image_path)

        # 自动增强
        if enhance:
            image = self.auto_enhance(image)

        # 二值化
        if binary:
            image = self.binarize(image, threshold=140)

        # 确定输出路径
        if output_path is None:
            path_obj = Path(image_path)
            output_path = str(
                path_obj.parent / f"{path_obj.stem}_preprocessed{path_obj.suffix}"
            )

        # 保存图像
        image.save(output_path, format=self.output_format, dpi=(self.dpi, self.dpi))

        logger.info(f"图像预处理完成: {output_path}")
        return output_path

    def batch_preprocess(
        self,
        image_paths: List[str],
        output_dir: str,
        enhance: bool = True,
    ) -> List[str]:
        """
        批量预处理图像

        Args:
            image_paths: 图像路径列表
            output_dir: 输出目录
            enhance: 是否增强

        Returns:
            预处理后的图像路径列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        processed_paths = []

        for idx, image_path in enumerate(image_paths):
            logger.info(f"预处理进度: {idx + 1}/{len(image_paths)}")
            try:
                path_obj = Path(image_path)
                output_path = output_dir / f"{path_obj.stem}_preprocessed{path_obj.suffix}"

                processed_path = self.preprocess_for_ocr(
                    image_path,
                    enhance=enhance,
                    output_path=str(output_path),
                )
                processed_paths.append(processed_path)

            except Exception as e:
                logger.error(f"图像预处理失败: {image_path}, 错误: {e}")

        logger.info(f"批量预处理完成,成功 {len(processed_paths)}/{len(image_paths)}")
        return processed_paths

    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        获取图像信息

        Args:
            image_path: 图像路径

        Returns:
            图像信息字典
        """
        image = self.load_image(image_path)
        path_obj = Path(image_path)

        return {
            "image_path": image_path,
            "file_name": path_obj.name,
            "file_size_bytes": path_obj.stat().st_size,
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
            "has_transparency": image.mode in ("RGBA", "LA") or "transparency" in image.info,
        }
