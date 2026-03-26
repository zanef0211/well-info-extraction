"""
清理临时文件和测试文件
"""
import os
import glob

# 需要删除的文件列表
FILES_TO_DELETE = [
    "fix_field_schemas.py",
    "fix_units.py",
    "fix_venv.py",
    "test_format_support.py",
    "test_langchain.py",
    "test_wellno_first.py",
]

# 检查并删除文件
def clean_temp_files():
    print("=" * 60)
    print("清理临时文件和测试文件")
    print("=" * 60)
    
    deleted_count = 0
    not_found_count = 0
    
    for file_name in FILES_TO_DELETE:
        file_path = os.path.join(os.getcwd(), file_name)
        
        if os.path.exists(file_path):
            try:
                # 获取文件大小
                file_size = os.path.getsize(file_path)
                
                # 删除文件
                os.remove(file_path)
                
                # 显示删除信息
                size_str = f"{file_size} bytes"
                if file_size > 1024:
                    size_str = f"{file_size / 1024:.2f} KB"
                if file_size > 1024 * 1024:
                    size_str = f"{file_size / (1024 * 1024):.2f} MB"
                
                print(f"✅ 已删除: {file_name} ({size_str})")
                deleted_count += 1
            except Exception as e:
                print(f"❌ 删除失败: {file_name} - {e}")
        else:
            print(f"⚠️  文件不存在: {file_name}")
            not_found_count += 1
    
    print("=" * 60)
    print(f"清理完成！")
    print(f"  已删除: {deleted_count} 个文件")
    print(f"  不存在: {not_found_count} 个文件")
    print("=" * 60)


if __name__ == "__main__":
    # 确认删除
    print("即将删除以下临时文件：")
    for file_name in FILES_TO_DELETE:
        print(f"  - {file_name}")
    
    print("\n⚠️  警告：这些文件将被永久删除！")
    
    confirm = input("\n确认删除？(yes/no): ")
    
    if confirm.lower() == 'yes':
        clean_temp_files()
        print("\n✅ 清理完成！")
    else:
        print("\n❌ 已取消清理操作")
