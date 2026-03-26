"""
诊断并修复导入问题
"""
import sys
import subprocess

def check_module(module_name):
    """检查模块是否可导入"""
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False

def main():
    print("=" * 60)
    print("诊断导入问题")
    print("=" * 60)

    # 检查关键依赖
    print("\n[1] 检查关键依赖:")
    required_modules = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'sqlalchemy',
        'psycopg2',
        'loguru',
        'requests',
        'python_multipart',
    ]

    missing_modules = []
    for module in required_modules:
        if not check_module(module):
            missing_modules.append(module)

    # 检查项目模块
    print("\n[2] 检查项目模块:")
    try:
        from config.prompts import Prompts
        print("✅ config.prompts.Prompts")
    except Exception as e:
        print(f"❌ config.prompts.Prompts: {e}")

    try:
        from config.field_schemas import FIELD_SCHEMAS
        print("✅ config.field_schemas.FIELD_SCHEMAS")
    except Exception as e:
        print(f"❌ config.field_schemas.FIELD_SCHEMAS: {e}")

    try:
        from api.schemas import SingleWellBatchRequest
        print("✅ api.schemas.SingleWellBatchRequest")
    except Exception as e:
        print(f"❌ api.schemas.SingleWellBatchRequest: {e}")

    try:
        from api.routes import router
        print("✅ api.routes.router")
    except Exception as e:
        print(f"❌ api.routes.router: {e}")

    try:
        from pipeline.extractor import DocumentExtractor
        print("✅ pipeline.extractor.DocumentExtractor")
    except Exception as e:
        print(f"❌ pipeline.extractor.DocumentExtractor: {e}")

    # 安装缺失的模块
    if missing_modules:
        print("\n[3] 安装缺失的模块:")
        for module in missing_modules:
            print(f"  安装 {module}...")
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', module],
                    check=True,
                    capture_output=True
                )
                print(f"  ✅ {module} 安装成功")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ {module} 安装失败: {e.stderr.decode()}")

    print("\n" + "=" * 60)
    print("诊断完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
