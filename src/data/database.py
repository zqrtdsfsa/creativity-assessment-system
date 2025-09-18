"""
数据库管理模块
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from src.data.models import StudentProfile, AssessmentResult, AssessmentSession, Question, Answer, CreativityScore
from src.core.config import Config
from src.core.logging_utils import get_app_logger

Base = declarative_base()
_db_log = get_app_logger("database")

class StudentProfileDB(Base):
    """学生档案数据库模型"""
    __tablename__ = "student_profiles"
    
    student_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    grade = Column(String, nullable=False)
    school = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AssessmentSessionDB(Base):
    """测评会话数据库模型"""
    __tablename__ = "assessment_sessions"
    
    session_id = Column(String, primary_key=True)
    student_id = Column(String, nullable=False)
    student_name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    questions = Column(JSON)  # 存储题目信息
    answers = Column(JSON)   # 存储答案信息
    status = Column(String, default="in_progress")

class AssessmentResultDB(Base):
    """测评结果数据库模型"""
    __tablename__ = "assessment_results"
    
    result_id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    student_id = Column(String, nullable=False)
    student_name = Column(String, nullable=False)
    total_score = Column(Float, nullable=False)
    dimension_scores = Column(JSON)  # 存储各维度得分
    overall_level = Column(String, nullable=False)
    recommendations = Column(JSON)   # 存储建议
    completed_at = Column(DateTime, nullable=False)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    # 学生档案管理
    def create_student_profile(self, profile: StudentProfile) -> bool:
        """创建学生档案"""
        try:
            session = self.get_session()
            db_profile = StudentProfileDB(
                student_id=profile.student_id,
                name=profile.name,
                age=profile.age,
                grade=profile.grade,
                school=profile.school,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
            session.add(db_profile)
            session.commit()
            session.close()
            _db_log.info("create_student_profile success: %s", profile.student_id)
            return True
        except Exception as e:
            _db_log.warning("create_student_profile failed for %s: %s", profile.student_id, e)
            return False
    
    def get_student_profile(self, student_id: str) -> Optional[StudentProfile]:
        """获取学生档案"""
        try:
            session = self.get_session()
            db_profile = session.query(StudentProfileDB).filter(
                StudentProfileDB.student_id == student_id
            ).first()
            _db_log.info("get_student_profile query: %s -> %s", student_id, bool(db_profile))
            
            if db_profile:
                profile = StudentProfile(
                    student_id=db_profile.student_id,
                    name=db_profile.name,
                    age=db_profile.age,
                    grade=db_profile.grade,
                    school=db_profile.school,
                    created_at=db_profile.created_at,
                    updated_at=db_profile.updated_at
                )
                session.close()
                return profile
            session.close()
            return None
        except Exception as e:
            _db_log.warning("get_student_profile failed for %s: %s", student_id, e)
            return None
    
    def update_student_profile(self, profile: StudentProfile) -> bool:
        """更新学生档案"""
        try:
            session = self.get_session()
            db_profile = session.query(StudentProfileDB).filter(
                StudentProfileDB.student_id == profile.student_id
            ).first()
            
            if db_profile:
                db_profile.name = profile.name
                db_profile.age = profile.age
                db_profile.grade = profile.grade
                db_profile.school = profile.school
                db_profile.updated_at = datetime.utcnow()
                session.commit()
                session.close()
                return True
            session.close()
            return False
        except Exception as e:
            print(f"更新学生档案失败: {e}")
            return False
    
    # 测评会话管理
    def create_assessment_session(self, session_data: AssessmentSession) -> bool:
        """创建测评会话"""
        try:
            session = self.get_session()
            db_session = AssessmentSessionDB(
                session_id=session_data.session_id,
                student_id=session_data.student_id,
                student_name=session_data.student_name,
                start_time=session_data.start_time,
                end_time=session_data.end_time,
                questions=[q.dict() for q in session_data.questions],
                answers=[a.dict() for a in session_data.answers],
                status=session_data.status
            )
            session.add(db_session)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"创建测评会话失败: {e}")
            return False
    
    def update_assessment_session(self, session_data: AssessmentSession) -> bool:
        """更新测评会话"""
        try:
            session = self.get_session()
            db_session = session.query(AssessmentSessionDB).filter(
                AssessmentSessionDB.session_id == session_data.session_id
            ).first()
            
            if db_session:
                db_session.end_time = session_data.end_time
                db_session.answers = [a.dict() for a in session_data.answers]
                db_session.status = session_data.status
                session.commit()
                session.close()
                return True
            session.close()
            return False
        except Exception as e:
            print(f"更新测评会话失败: {e}")
            return False
    
    def get_assessment_session(self, session_id: str) -> Optional[AssessmentSession]:
        """获取测评会话"""
        try:
            session = self.get_session()
            db_session = session.query(AssessmentSessionDB).filter(
                AssessmentSessionDB.session_id == session_id
            ).first()
            
            if db_session:
                # 重建Question和Answer对象
                questions = []
                for q_data in db_session.questions:
                    questions.append(Question(**q_data))
                
                answers = []
                for a_data in db_session.answers:
                    a_data['timestamp'] = datetime.fromisoformat(a_data['timestamp'])
                    answers.append(Answer(**a_data))
                
                session_data = AssessmentSession(
                    session_id=db_session.session_id,
                    student_id=db_session.student_id,
                    student_name=db_session.student_name,
                    start_time=db_session.start_time,
                    end_time=db_session.end_time,
                    questions=questions,
                    answers=answers,
                    status=db_session.status
                )
                session.close()
                return session_data
            session.close()
            return None
        except Exception as e:
            print(f"获取测评会话失败: {e}")
            return None
    
    # 测评结果管理
    def save_assessment_result(self, result: AssessmentResult) -> bool:
        """保存测评结果"""
        try:
            session = self.get_session()
            db_result = AssessmentResultDB(
                result_id=f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                session_id=result.session_id,
                student_id=result.student_id,
                student_name=result.student_name,
                total_score=result.total_score,
                dimension_scores=[s.dict() for s in result.dimension_scores],
                overall_level=result.overall_level,
                recommendations=result.recommendations,
                completed_at=result.completed_at
            )
            session.add(db_result)
            session.commit()
            session.close()
            _db_log.info("save_assessment_result success: session=%s total=%.2f", result.session_id, result.total_score)
            return True
        except Exception as e:
            _db_log.exception("save_assessment_result failed: session=%s error=%s", result.session_id, e)
            return False
    
    def get_assessment_results(self, student_id: str) -> List[AssessmentResult]:
        """获取学生的所有测评结果"""
        try:
            session = self.get_session()
            db_results = session.query(AssessmentResultDB).filter(
                AssessmentResultDB.student_id == student_id
            ).order_by(AssessmentResultDB.completed_at.desc()).all()
            
            results = []
            for db_result in db_results:
                # 重建CreativityScore对象
                dimension_scores = []
                for score_data in db_result.dimension_scores:
                    dimension_scores.append(CreativityScore(**score_data))
                
                result = AssessmentResult(
                    session_id=db_result.session_id,
                    student_id=db_result.student_id,
                    student_name=db_result.student_name,
                    total_score=db_result.total_score,
                    dimension_scores=dimension_scores,
                    overall_level=db_result.overall_level,
                    recommendations=db_result.recommendations,
                    completed_at=db_result.completed_at
                )
                results.append(result)
            
            session.close()
            return results
        except Exception as e:
            print(f"获取测评结果失败: {e}")
            return []
    
    def get_all_assessment_results(self) -> List[AssessmentResult]:
        """获取所有测评结果"""
        try:
            session = self.get_session()
            db_results = session.query(AssessmentResultDB).order_by(
                AssessmentResultDB.completed_at.desc()
            ).all()
            
            results = []
            for db_result in db_results:
                dimension_scores = []
                for score_data in db_result.dimension_scores:
                    dimension_scores.append(CreativityScore(**score_data))
                
                result = AssessmentResult(
                    session_id=db_result.session_id,
                    student_id=db_result.student_id,
                    student_name=db_result.student_name,
                    total_score=db_result.total_score,
                    dimension_scores=dimension_scores,
                    overall_level=db_result.overall_level,
                    recommendations=db_result.recommendations,
                    completed_at=db_result.completed_at
                )
                results.append(result)
            
            session.close()
            return results
        except Exception as e:
            print(f"获取所有测评结果失败: {e}")
            return []
    
    def get_peer_results(self, student_grade: str, exclude_student_id: str = None) -> List[AssessmentResult]:
        """获取同龄人测评结果"""
        try:
            session = self.get_session()
            
            # 先获取同年级的学生ID
            student_profiles = session.query(StudentProfileDB).filter(
                StudentProfileDB.grade == student_grade
            ).all()
            
            student_ids = [p.student_id for p in student_profiles]
            if exclude_student_id:
                student_ids = [sid for sid in student_ids if sid != exclude_student_id]
            
            if not student_ids:
                session.close()
                return []
            
            # 获取这些学生的测评结果
            db_results = session.query(AssessmentResultDB).filter(
                AssessmentResultDB.student_id.in_(student_ids)
            ).order_by(AssessmentResultDB.completed_at.desc()).all()
            
            results = []
            for db_result in db_results:
                dimension_scores = []
                for score_data in db_result.dimension_scores:
                    dimension_scores.append(CreativityScore(**score_data))
                
                result = AssessmentResult(
                    session_id=db_result.session_id,
                    student_id=db_result.student_id,
                    student_name=db_result.student_name,
                    total_score=db_result.total_score,
                    dimension_scores=dimension_scores,
                    overall_level=db_result.overall_level,
                    recommendations=db_result.recommendations,
                    completed_at=db_result.completed_at
                )
                results.append(result)
            
            session.close()
            return results
        except Exception as e:
            print(f"获取同龄人测评结果失败: {e}")
            return []
