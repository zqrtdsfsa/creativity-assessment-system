"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class QuestionType(str, Enum):
    """题目类型枚举"""
    DIVERGENT_THINKING = "divergent_thinking"
    CONVERGENT_THINKING = "convergent_thinking"
    CREATIVE_PROBLEM_SOLVING = "creative_problem_solving"
    IMAGINATION = "imagination"

class CreativityDimension(str, Enum):
    """创造力维度枚举"""
    FLUENCY = "fluency"
    FLEXIBILITY = "flexibility"
    ORIGINALITY = "originality"
    ELABORATION = "elaboration"

class Question(BaseModel):
    """测评题目模型"""
    id: str
    type: QuestionType
    title: str
    content: str
    time_limit: int = 300  # 秒
    dimensions: List[CreativityDimension]
    scoring_criteria: Dict[str, Any]

class Answer(BaseModel):
    """学生答案模型"""
    question_id: str
    student_id: str
    content: str
    timestamp: datetime
    time_spent: int  # 秒

class AssessmentSession(BaseModel):
    """测评会话模型"""
    session_id: str
    student_id: str
    student_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    questions: List[Question]
    answers: List[Answer] = []
    status: str = "in_progress"  # in_progress, completed, abandoned

class CreativityScore(BaseModel):
    """创造力评分模型"""
    dimension: CreativityDimension
    score: float
    max_score: float
    percentage: float

class AssessmentResult(BaseModel):
    """测评结果模型"""
    session_id: str
    student_id: str
    student_name: str
    total_score: float
    dimension_scores: List[CreativityScore]
    overall_level: str  # 优秀, 良好, 一般, 需要提升
    recommendations: List[str]
    completed_at: datetime

class StudentProfile(BaseModel):
    """学生档案模型"""
    student_id: str
    name: str
    age: int
    grade: str
    school: str
    assessment_history: List[AssessmentResult] = []
    created_at: datetime
    updated_at: datetime
