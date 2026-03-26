"""
自定义异常
"""


class WellInfoException(Exception):
    """基础异常类"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class FileError(WellInfoException):
    """文件处理异常"""
    pass


class ParsingError(WellInfoException):
    """解析异常"""
    pass


class ImageError(WellInfoException):
    """图像处理异常"""
    pass


class OCRError(WellInfoException):
    """OCR异常"""
    pass


class LLMError(WellInfoException):
    """LLM异常"""
    pass


class ModelError(WellInfoException):
    """模型异常"""
    pass


class ModelException(WellInfoException):
    """模型异常（别名）"""
    pass


class DocumentParseException(WellInfoException):
    """文档解析异常"""
    pass


class ValidationException(WellInfoException):
    """校验异常"""
    pass


class ConfigurationException(WellInfoException):
    """配置异常"""
    pass


class APIException(WellInfoException):
    """API异常"""
    pass


class DatabaseError(WellInfoException):
    """数据库异常"""
    pass


class PipelineError(WellInfoException):
    """管道异常"""
    pass


class ProcessingError(WellInfoException):
    """处理异常"""
    pass


class ClassificationError(WellInfoException):
    """分类异常"""
    pass


class ExtractionError(WellInfoException):
    """提取异常"""
    pass
