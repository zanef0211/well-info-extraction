"""
诊断导入问题
"""
import sys

print("=" * 60)
print("诊断导入问题")
print("=" * 60)

# 显示 Python 路径
print("\n[1] Python 路径:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

# 检查 loguru
print("\n[2] 检查 loguru:")
try:
    import loguru
    print(f"  ✅ loguru 已安装")
    print(f"  版本: {loguru.__version__}")
    print(f"  路径: {loguru.__file__}")
except ImportError as e:
    print(f"  ❌ loguru 未安装: {e}")

# 检查 loguru.logger
print("\n[3] 检查 loguru.logger:")
try:
    from loguru import logger
    print(f"  ✅ logger 导入成功")
except Exception as e:
    print(f"  ❌ logger 导入失败: {e}")

# 检查配置
print("\n[4] 检查配置:")
try:
    from config.settings import get_settings
    settings = get_settings()
    print(f"  ✅ 配置加载成功")
    print(f"  DEBUG: {settings.DEBUG}")
except Exception as e:
    print(f"  ❌ 配置加载失败: {e}")

# 检查 utils.logger
print("\n[5] 检查 utils.logger:")
try:
    from utils.logger import get_logger
    print(f"  ✅ utils.logger 导入成功")
except Exception as e:
    print(f"  ❌ utils.logger 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 检查 utils.exceptions
print("\n[6] 检查 utils.exceptions:")
try:
    from utils.exceptions import ProcessingError, ExtractionError
    print(f"  ✅ utils.exceptions 导入成功")
except Exception as e:
    print(f"  ❌ utils.exceptions 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成！")
print("=" * 60)
