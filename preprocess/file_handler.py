"""
文件处理器 - 处理文件上传、验证、存储
"""
import logging
import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import mimetypes

from utils.logger import get_logger
from utils.exceptions import FileError

logger = get_logger(__name__)


class FileHandler:
    """文件处理器 - 负责文件上传、验证和存储"""

    # 支持的文件类型
    ALLOWED_EXTENSIONS = {
        # PDF文档
        ".pdf": "application/pdf",
        # Word文档
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        # Excel文档
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        # 文本文件
        ".txt": "text/plain",
        # 图像文件
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }

    # 最大文件大小 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    def __init__(
        self,
        upload_dir: str = "storage/uploads",
        processed_dir: str = "storage/processed",
    ):
        """
        初始化文件处理器

        Args:
            upload_dir: 上传文件目录
            processed_dir: 处理后文件目录
        """
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)

        # 创建目录
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"文件处理器初始化完成,上传目录: {self.upload_dir}")

    def validate_file(
        self,
        file_path: str,
        check_size: bool = True,
        check_type: bool = True,
    ) -> Dict[str, Any]:
        """
        验证文件

        Args:
            file_path: 文件路径
            check_size: 是否检查文件大小
            check_type: 是否检查文件类型

        Returns:
            验证结果字典

        Raises:
            FileError: 验证失败时抛出
        """
        path = Path(file_path)

        # 检查文件是否存在
        if not path.exists():
            raise FileError(f"文件不存在: {file_path}")

        # 检查文件大小
        file_size = path.stat().st_size
        if check_size and file_size > self.MAX_FILE_SIZE:
            raise FileError(
                f"文件大小超过限制: {file_size / (1024*1024):.2f}MB "
                f"(最大: {self.MAX_FILE_SIZE / (1024*1024):.2f}MB)"
            )

        # 检查文件扩展名
        file_ext = path.suffix.lower()
        if check_type and file_ext not in self.ALLOWED_EXTENSIONS:
            raise FileError(
                f"不支持的文件类型: {file_ext}, "
                f"支持的类型: {', '.join(self.ALLOWED_EXTENSIONS.keys())}"
            )

        # 获取文件MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        expected_mime = self.ALLOWED_EXTENSIONS.get(file_ext)

        logger.info(f"文件验证通过: {file_path}, 大小: {file_size / 1024:.2f}KB")

        return {
            "valid": True,
            "file_path": file_path,
            "file_size": file_size,
            "file_extension": file_ext,
            "mime_type": mime_type,
            "expected_mime_type": expected_mime,
        }

    def calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件MD5哈希值

        Args:
            file_path: 文件路径

        Returns:
            MD5哈希值(十六进制字符串)
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)

        hash_value = md5_hash.hexdigest()
        logger.debug(f"文件哈希: {file_path} -> {hash_value}")
        return hash_value

    def save_uploaded_file(
        self,
        file_data: bytes,
        filename: str,
        subfolder: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        保存上传的文件

        Args:
            file_data: 文件二进制数据
            filename: 文件名
            subfolder: 子文件夹(可选,按日期组织)

        Returns:
            保存结果字典,包含file_path等信息
        """
        # 确定保存路径
        if subfolder:
            save_dir = self.upload_dir / subfolder
        else:
            save_dir = self.upload_dir / datetime.now().strftime("%Y%m%d")

        save_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        file_ext = Path(filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"

        # 保存文件
        file_path = save_dir / unique_filename
        with open(file_path, "wb") as f:
            f.write(file_data)

        # 验证保存的文件
        validation = self.validate_file(str(file_path))

        # 计算哈希
        file_hash = self.calculate_file_hash(str(file_path))

        logger.info(f"文件保存成功: {file_path}")

        return {
            "file_path": str(file_path),
            "file_hash": file_hash,
            "original_filename": filename,
            "saved_filename": unique_filename,
            **validation,
        }

    def save_processed_file(
        self,
        file_data: bytes,
        original_path: str,
        suffix: str = "_processed",
        extension: Optional[str] = None,
    ) -> str:
        """
        保存处理后的文件

        Args:
            file_data: 文件数据
            original_path: 原始文件路径
            suffix: 文件名后缀
            extension: 新文件扩展名(可选)

        Returns:
            保存后的文件路径
        """
        original_path = Path(original_path)
        filename = original_path.stem + suffix
        if extension:
            filename += extension
        else:
            filename += original_path.suffix

        save_path = self.processed_dir / filename

        with open(save_path, "wb") as f:
            f.write(file_data)

        logger.info(f"处理后文件保存成功: {save_path}")
        return str(save_path)

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        path = Path(file_path)

        if not path.exists():
            raise FileError(f"文件不存在: {file_path}")

        stat = path.stat()

        return {
            "file_path": file_path,
            "file_name": path.name,
            "file_size": stat.st_size,
            "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
            "file_extension": path.suffix.lower(),
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "file_hash": self.calculate_file_hash(file_path),
        }

    def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功删除
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"文件不存在,无需删除: {file_path}")
            return False

        try:
            path.unlink()
            logger.info(f"文件删除成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败: {e}", exc_info=True)
            raise FileError(f"文件删除失败: {str(e)}") from e

    def clean_old_files(
        self,
        days: int = 7,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        清理旧文件

        Args:
            days: 保留天数
            dry_run: 是否仅模拟运行

        Returns:
            清理结果
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        deleted_size = 0
        deleted_files = []

        # 扫描上传目录
        for file_path in self.upload_dir.rglob("*"):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_time:
                    deleted_count += 1
                    deleted_size += file_path.stat().st_size
                    deleted_files.append(str(file_path))

                    if not dry_run:
                        try:
                            file_path.unlink()
                        except Exception as e:
                            logger.error(f"删除文件失败: {file_path}, {e}")

        logger.info(
            f"清理完成: {'模拟' if dry_run else '实际'}删除 "
            f"{deleted_count} 个文件,释放空间: {deleted_size / (1024*1024):.2f}MB"
        )

        return {
            "deleted_count": deleted_count,
            "deleted_size_mb": round(deleted_size / (1024 * 1024), 2),
            "deleted_files": deleted_files[:100],  # 最多返回100个
            "dry_run": dry_run,
        }
