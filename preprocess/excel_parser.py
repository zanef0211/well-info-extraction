"""
Excel文档解析器 - 解析XLSX/XLS文件
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pandas as pd
except ImportError:
    pd = None

from utils.logger import get_logger
from utils.exceptions import ParsingError

logger = get_logger(__name__)


class ExcelParser:
    """Excel文档解析器 - 使用pandas解析Excel文件"""

    def __init__(self):
        """初始化Excel解析器"""
        if pd is None:
            raise ParsingError("pandas未安装,请先安装: pip install pandas openpyxl")
        logger.info("Excel文档解析器初始化完成")

    def extract_text(self, excel_path: str) -> str:
        """
        提取Excel文档中的所有文本

        Args:
            excel_path: Excel文档路径

        Returns:
            完整文本内容

        Raises:
            ParsingError: 解析失败时抛出
        """
        try:
            logger.info(f"开始提取Excel文档文本: {excel_path}")

            # 读取所有工作表
            excel_file = pd.ExcelFile(excel_path)
            sheet_texts = []

            for sheet_name in excel_file.sheet_names:
                # 读取工作表
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                # 转换为文本
                sheet_text = self._dataframe_to_text(df, sheet_name)
                sheet_texts.append(sheet_text)

            full_text = "\n\n".join(sheet_texts)

            logger.info(
                f"Excel文档文本提取完成,工作表数: {len(excel_file.sheet_names)}"
            )
            return full_text

        except Exception as e:
            logger.error(f"Excel文档文本提取失败: {e}", exc_info=True)
            raise ParsingError(f"Excel文档文本提取失败: {str(e)}") from e

    def _dataframe_to_text(self, df: pd.DataFrame, sheet_name: str) -> str:
        """
        将DataFrame转换为文本

        Args:
            df: DataFrame对象
            sheet_name: 工作表名称

        Returns:
            文本内容
        """
        lines = []
        lines.append(f"[工作表: {sheet_name}]")

        # 添加表头
        if not df.empty:
            headers = " | ".join(str(col) for col in df.columns)
            lines.append(f"表头: {headers}")

            # 添加数据行
            for idx, row in df.iterrows():
                row_text = " | ".join(
                    str(val) if pd.notna(val) else ""
                    for val in row
                )
                lines.append(row_text)

        return "\n".join(lines)

    def extract_sheets(self, excel_path: str) -> List[Dict[str, Any]]:
        """
        提取所有工作表数据

        Args:
            excel_path: Excel文档路径

        Returns:
            工作表数据列表
        """
        try:
            excel_file = pd.ExcelFile(excel_path)
            sheets_data = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                sheets_data.append({
                    "sheet_name": sheet_name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "data": df.to_dict("records"),  # 转换为记录列表
                })

            logger.info(f"工作表提取完成,共 {len(sheets_data)} 个工作表")
            return sheets_data

        except Exception as e:
            logger.error(f"Excel文档工作表提取失败: {e}", exc_info=True)
            raise ParsingError(f"Excel文档工作表提取失败: {str(e)}") from e

    def extract_sheet_by_name(
        self,
        excel_path: str,
        sheet_name: str,
    ) -> Dict[str, Any]:
        """
        按名称提取工作表

        Args:
            excel_path: Excel文档路径
            sheet_name: 工作表名称

        Returns:
            工作表数据
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

            return {
                "sheet_name": sheet_name,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "data": df.to_dict("records"),
            }

        except Exception as e:
            logger.error(f"提取工作表失败: {sheet_name}, {e}", exc_info=True)
            raise ParsingError(f"提取工作表失败: {sheet_name}, {str(e)}") from e

    def get_excel_info(self, excel_path: str) -> Dict[str, Any]:
        """
        获取Excel文档信息

        Args:
            excel_path: Excel文档路径

        Returns:
            文档信息字典
        """
        try:
            excel_file = pd.ExcelFile(excel_path)
            path_obj = Path(excel_path)

            sheets_info = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets_info.append({
                    "name": sheet_name,
                    "rows": len(df),
                    "columns": len(df.columns),
                })

            return {
                "file_path": excel_path,
                "file_name": path_obj.name,
                "file_size": path_obj.stat().st_size,
                "file_size_mb": round(path_obj.stat().st_size / (1024 * 1024), 2),
                "total_sheets": len(excel_file.sheet_names),
                "sheet_names": excel_file.sheet_names,
                "sheets_info": sheets_info,
            }

        except Exception as e:
            logger.error(f"获取Excel文档信息失败: {e}", exc_info=True)
            raise ParsingError(f"获取Excel文档信息失败: {str(e)}") from e

    def extract_cells_with_data(
        self,
        excel_path: str,
        sheet_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        提含有数据的单元格

        Args:
            excel_path: Excel文档路径
            sheet_name: 工作表名称(可选,默认第一个)

        Returns:
            单元格数据列表
        """
        try:
            # 读取Excel
            if sheet_name:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(excel_path)

            cells_data = []

            # 遍历所有单元格
            for col_idx, col_name in enumerate(df.columns):
                for row_idx, value in df[col_name].items():
                    if pd.notna(value) and str(value).strip():
                        cells_data.append({
                            "sheet": sheet_name or "Sheet1",
                            "column": col_name,
                            "column_index": col_idx,
                            "row": row_idx + 2,  # +2因为pandas从0开始,且第一行是表头
                            "value": str(value),
                        })

            logger.info(f"提取到 {len(cells_data)} 个非空单元格")
            return cells_data

        except Exception as e:
            logger.error(f"提取单元格数据失败: {e}", exc_info=True)
            raise ParsingError(f"提取单元格数据失败: {str(e)}") from e
