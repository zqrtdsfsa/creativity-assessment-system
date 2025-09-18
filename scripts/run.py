#!/usr/bin/env python3
"""
学生创造力测评系统启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path


def check_requirements():
    """检查依赖是否安装"""
    try:
        import streamlit
        import langgraph
        import langchain
        import plotly
        import pandas
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False


def check_env_file():
    """检查环境变量文件"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  未找到.env文件")
        print("请复制env_example.txt为.env并配置 SILICONFLOW_API_KEY")
        return False
    
    # 简单检查API Key占位符
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if "your_openai_api_key_here" in content:
            print("⚠️  请配置有效的 API Key")
            return False
    
    print("✅ 环境配置正确")
    return True


def main():
    """主函数"""
    print("🎨 学生创造力测评系统")
    print("=" * 50)
    
    # 检查依赖
    if not check_requirements():
        sys.exit(1)
    
    # 检查环境配置
    if not check_env_file():
        print("\n请完成环境配置后重新运行")
        sys.exit(1)
    
    print("\n🚀 启动应用...")
    print("访问地址: http://localhost:8501")
    print("按 Ctrl+C 停止应用")
    print("=" * 50)
    
    # 启动Streamlit应用
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "src/app/app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
