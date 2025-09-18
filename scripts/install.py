#!/usr/bin/env python3
"""
学生创造力测评系统 - 自动安装脚本
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本: {sys.version.split()[0]}")
    return True

def install_requirements():
    """安装依赖包"""
    print("📦 安装依赖包...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False

def setup_env_file():
    """设置环境变量文件"""
    print("🔧 设置环境变量文件...")
    
    env_file = Path(".env")
    env_example = Path(".env")
    
    if env_file.exists():
        print("✅ .env文件已存在")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ 已创建.env文件")
        print("⚠️  请编辑.env文件，添加你的OpenAI API Key")
        return True
    else:
        print("❌ 未找到env_example.txt文件")
        return False

def create_directories():
    """创建必要的目录"""
    print("📁 创建目录结构...")
    
    directories = ["data", "logs", "exports"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def test_installation():
    """测试安装"""
    print("🧪 测试安装...")
    try:
        result = subprocess.run([
            sys.executable, "test_system.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 安装测试通过")
            return True
        else:
            print("❌ 安装测试失败")
            print("错误输出:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def show_next_steps():
    """显示后续步骤"""
    print("\n" + "=" * 60)
    print("🎉 安装完成！")
    print("\n📝 后续步骤:")
    print("1. 编辑 .env 文件，添加你的OpenAI API Key")
    print("2. 运行测试: python test_system.py")
    print("3. 运行演示: python demo.py")
    print("4. 启动应用: python run.py")
    print("5. 访问: http://localhost:8501")
    print("\n📚 更多信息请查看 README.md")

def main():
    """主安装函数"""
    print("🎨 学生创造力测评系统 - 自动安装")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖
    if not install_requirements():
        print("❌ 安装失败，请手动安装依赖包")
        sys.exit(1)
    
    # 设置环境文件
    if not setup_env_file():
        print("❌ 环境文件设置失败")
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 测试安装
    if not test_installation():
        print("⚠️  安装测试失败，但系统可能仍可正常使用")
    
    # 显示后续步骤
    show_next_steps()

if __name__ == "__main__":
    main()
