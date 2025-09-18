"""
学生创造力测评系统配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""
    
    # OpenAI配置
    base_url = os.getenv("SILICONFLOW_BASE_URL")
    api_key = os.getenv("SILICONFLOW_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("SILICONFLOW_API_KEY", ""))

    # 双Agent模型配置（若未设置则回退到 model_name）
    model_name_a = os.environ.get("SILICONFLOW_MODEL_CHAT_A")
    model_name_b = os.environ.get("SILICONFLOW_MODEL_CHAT_B")
    
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./creativity_assessment.db")
    
    # 应用配置
    APP_NAME = "学生创造力测评系统"
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # 测评配置
    MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS", 10))
    TIME_LIMIT_MINUTES = int(os.getenv("TIME_LIMIT_MINUTES", 30))
    
    # 创造力测评维度
    CREATIVITY_DIMENSIONS = {
        "fluency": "流畅性",  # 产生想法的数量
        "flexibility": "灵活性",  # 想法的多样性
        "originality": "独创性",  # 想法的独特性
        "elaboration": "精细性"  # 想法的详细程度
    }
    
    # 测评题目类型
    QUESTION_TYPES = {
        "divergent_thinking": "发散思维题",
        "convergent_thinking": "聚合思维题", 
        "creative_problem_solving": "创造性问题解决",
        "imagination": "想象力测试"
    }
