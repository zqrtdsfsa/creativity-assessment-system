#!/usr/bin/env python3
"""
系统测试脚本
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from src.data.models import StudentProfile

# 加载环境变量
load_dotenv()

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        from src.core.creativity_graph import CreativityAssessmentGraph
        from src.analysis.analysis import CreativityAnalyzer
        from src.data.database import DatabaseManager
        from src.data.models import StudentProfile, AssessmentResult, CreativityScore, CreativityDimension
        from src.core.config import Config
        print("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_database():
    """测试数据库连接"""
    print("测试数据库连接...")
    try:
        from src.data.database import DatabaseManager
        db = DatabaseManager()
        
        # 测试创建学生档案
        test_profile = StudentProfile(
            student_id=f"test_{int(datetime.now().timestamp())}",
            name="测试学生",
            age=12,
            grade="六年级",
            school="测试学校",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = db.create_student_profile(test_profile)
        if result:
            print("✅ 数据库连接正常")
            return True
        else:
            print("❌ 数据库操作失败")
            return False
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_config():
    """测试配置"""
    print("测试配置...")
    try:
        from src.core.config import Config
        
        print(f"应用名称: {Config.APP_NAME}")
        print(f"最大题目数: {Config.MAX_QUESTIONS}")
        print(f"时间限制: {Config.TIME_LIMIT_MINUTES}分钟")
        print(f"数据库URL: {Config.DATABASE_URL}")
        
        if Config.api_key:
            print("✅ 模型 API Key 已配置")
        else:
            print("⚠️  模型 API Key 未配置")
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_creativity_graph():
    """测试创造力测评图"""
    print("测试创造力测评图...")
    try:
        from src.core.creativity_graph import CreativityAssessmentGraph
        
        # 检查API Key
        if not os.getenv("SILICONFLOW_API_KEY"):
            print("⚠️  跳过LangGraph测试（需要模型 API Key）")
            return True
        
        graph = CreativityAssessmentGraph()
        print("✅ 创造力测评图创建成功")
        return True
    except Exception as e:
        print(f"❌ 创造力测评图测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 学生创造力测评系统 - 系统测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置检查", test_config),
        ("数据库连接", test_database),
        ("创造力测评图", test_creativity_graph),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常运行")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
