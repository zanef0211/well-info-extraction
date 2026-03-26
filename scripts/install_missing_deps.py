"""
安装缺失的依赖
"""
import subprocess
import sys

print("=" * 60)
print("安装缺失的依赖")
print("=" * 60)

# 必需的包
packages = [
    'loguru==0.7.3',
    'fastapi==0.135.2',
    'uvicorn[standard]==0.42.0',
    'pydantic==2.12.5',
    'python-multipart==0.0.22',
]

for package in packages:
    print(f"安装 {package}...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"  ✅ 安装成功")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ 安装失败:")
        print(f"    {e.stderr}")

print("\n" + "=" * 60)
print("安装完成！")
print("=" * 60)
print("\n现在可以运行: python main.py")
