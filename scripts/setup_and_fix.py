"""
综合修复脚本：安装依赖并验证导入
"""
import subprocess
import sys

def run_command(cmd, description):
    """执行命令"""
    print(f"\n{description}")
    print("-" * 60)
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            shell=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("综合修复脚本")
    print("=" * 60)

    # 1. 升级 pip
    print("\n[1/3] 升级 pip...")
    run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "升级 pip"
    )

    # 2. 安装核心依赖
    print("\n[2/3] 安装核心依赖...")
    core_packages = [
        "loguru==0.7.3",
        "fastapi==0.135.2",
        "uvicorn[standard]==0.42.0",
        "pydantic==2.12.5",
        "python-multipart==0.0.22",
        "python-dotenv==1.2.2",
        "sqlalchemy==2.0.48",
        "psycopg2-binary==2.9.11",
        "requests==2.32.5",
    ]

    for package in core_packages:
        print(f"安装 {package}...")
        run_command(
            f"{sys.executable} -m pip install {package}",
            f"安装 {package}"
        )

    # 3. 验证导入
    print("\n[3/3] 验证关键导入...")
    imports_to_check = [
        ("loguru", "from loguru import logger"),
        ("fastapi", "from fastapi import FastAPI"),
        ("uvicorn", "import uvicorn"),
        ("pydantic", "from pydantic import BaseModel"),
        ("config.prompts", "from config.prompts import Prompts"),
        ("config.field_schemas", "from config.field_schemas import FIELD_SCHEMAS"),
        ("api.schemas", "from api.schemas import SingleWellBatchRequest"),
    ]

    for name, import_stmt in imports_to_check:
        try:
            exec(import_stmt)
            print(f"  OK: {name}")
        except Exception as e:
            print(f"  FAIL: {name} - {e}")

    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)
    print("\n现在可以运行: python main.py")

if __name__ == "__main__":
    main()
