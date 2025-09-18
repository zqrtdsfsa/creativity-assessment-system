#!/usr/bin/env python3
"""
学生创造力测评系统演示脚本
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def demo_models():
    """演示数据模型"""
    print("📋 演示数据模型...")
    
    from src.data.models import StudentProfile, AssessmentResult, CreativityScore, CreativityDimension
    
    # 创建学生档案
    student = StudentProfile(
        student_id="demo_001",
        name="张三",
        age=12,
        grade="六年级",
        school="演示学校",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    print(f"学生档案: {student.name} ({student.grade})")
    
    # 创建创造力评分
    scores = []
    for dimension in CreativityDimension:
        score = CreativityScore(
            dimension=dimension,
            score=8.5,
            max_score=10.0,
            percentage=85.0
        )
        scores.append(score)
    
    # 创建测评结果
    result = AssessmentResult(
        session_id="demo_session",
        student_id=student.student_id,
        student_name=student.name,
        total_score=34.0,
        dimension_scores=scores,
        overall_level="优秀",
        recommendations=["继续保持创新思维！"],
        completed_at=datetime.now()
    )
    
    print(f"测评结果: 总分 {result.total_score}, 等级 {result.overall_level}")
    print("✅ 数据模型演示完成")

def demo_database():
    """演示数据库功能"""
    print("\n🗄️ 演示数据库功能...")
    
    try:
        from src.data.database import DatabaseManager
        from src.data.models import StudentProfile, AssessmentResult, CreativityScore, CreativityDimension
        from datetime import datetime
        
        db = DatabaseManager()
        
        # 创建测试学生
        test_student = StudentProfile(
            student_id="demo_002",
            name="李四",
            age=13,
            grade="七年级",
            school="测试学校",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存学生档案
        if db.create_student_profile(test_student):
            print("✅ 学生档案保存成功")
        else:
            print("⚠️ 学生档案已存在")
        
        # 查询学生档案
        retrieved_student = db.get_student_profile("demo_002")
        if retrieved_student:
            print(f"✅ 查询到学生: {retrieved_student.name}")
        
        print("✅ 数据库功能演示完成")
        
    except Exception as e:
        print(f"❌ 数据库演示失败: {e}")

def demo_analysis():
    """演示分析功能"""
    print("\n📊 演示分析功能...")
    
    try:
        from src.analysis.analysis import CreativityAnalyzer
        from src.data.models import AssessmentResult, CreativityScore, CreativityDimension
        from datetime import datetime
        
        analyzer = CreativityAnalyzer()
        
        # 创建测试结果
        scores = []
        for dimension in CreativityDimension:
            score = CreativityScore(
                dimension=dimension,
                score=7.5,
                max_score=10.0,
                percentage=75.0
            )
            scores.append(score)
        
        result = AssessmentResult(
            session_id="demo_analysis",
            student_id="demo_003",
            student_name="王五",
            total_score=30.0,
            dimension_scores=scores,
            overall_level="良好",
            recommendations=["继续努力提升创造力"],
            completed_at=datetime.now()
        )
        
        # 分析结果
        analysis = analyzer.analyze_single_result(result)
        print(f"✅ 分析完成: 总分 {analysis['overall_scores']['total_score']}")
        print(f"等级: {analysis['overall_scores']['level']}")
        
        print("✅ 分析功能演示完成")
        
    except Exception as e:
        print(f"❌ 分析演示失败: {e}")

def demo_config():
    """演示配置功能"""
    print("\n⚙️ 演示配置功能...")
    
    try:
        from src.core.config import Config
        
        print(f"应用名称: {Config.APP_NAME}")
        print(f"最大题目数: {Config.MAX_QUESTIONS}")
        print(f"时间限制: {Config.TIME_LIMIT_MINUTES}分钟")
        print(f"创造力维度: {list(Config.CREATIVITY_DIMENSIONS.values())}")
        print(f"题目类型: {list(Config.QUESTION_TYPES.values())}")
        
        print("✅ 配置功能演示完成")
        
    except Exception as e:
        print(f"❌ 配置演示失败: {e}")

def main():
    """主演示函数"""
    print("🎨 学生创造力测评系统 - 功能演示")
    print("=" * 60)
    
    # 检查环境
    if not os.getenv("SILICONFLOW_API_KEY"):
        print("⚠️  未配置模型 API Key，部分功能可能无法使用")
        print("请设置环境变量 SILICONFLOW_API_KEY")
        print()
    
    # 运行演示
    demos = [
        ("数据模型", demo_models),
        ("数据库功能", demo_database),
        ("分析功能", demo_analysis),
        ("配置功能", demo_config),
    ]
    
    for demo_name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"❌ {demo_name}演示失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("\n📝 下一步:")
    print("1. 配置 SILICONFLOW_API_KEY")
    print("2. 运行 'python scripts/run.py' 启动Web应用")
    print("3. 访问 http://localhost:8501 使用系统")

if __name__ == "__main__":
    main()
