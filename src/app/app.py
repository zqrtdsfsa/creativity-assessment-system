"""
学生创造力测评系统 - Streamlit Web应用
"""
from typing import List

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
import uuid

from src.core.creativity_graph import CreativityAssessmentGraph
from src.analysis.analysis import CreativityAnalyzer
from src.data.database import DatabaseManager
from src.data.models import StudentProfile, AssessmentResult, CreativityScore, CreativityDimension
from src.core.config import Config
from src.core.logging_utils import get_app_logger

# 页面配置
st.set_page_config(
    page_title="学生创造力测评系统",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化
@st.cache_resource
def init_components():
    """初始化组件"""
    return {
        "graph": CreativityAssessmentGraph(),
        "analyzer": CreativityAnalyzer(),
        "db": DatabaseManager()
    }

components = init_components()
_app_log = get_app_logger("app")

def main():
    """主应用函数"""
    st.title("🎨 学生创造力测评系统")
    st.markdown("基于LangGraph的智能创造力评估平台")
    
    # 侧边栏导航
    page = st.sidebar.selectbox(
        "选择功能",
        ["学生测评", "结果分析", "学生管理", "系统设置"]
    )
    
    if page == "学生测评":
        student_assessment_page()
    elif page == "结果分析":
        result_analysis_page()
    elif page == "学生管理":
        student_management_page()
    elif page == "系统设置":
        system_settings_page()

def student_assessment_page():
    """学生测评页面"""
    st.header("📝 创造力测评")

    # 若测评进行中，直接显示测评界面（处理 rerun 后未再次调用 start_assessment 的情况）
    if st.session_state.get("assessment_in_progress", False):
        display_assessment_interface()
        return

    # 学生信息输入
    with st.expander("学生信息", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("姓名", placeholder="请输入学生姓名")
            student_id = st.text_input("学号", placeholder="请输入学号")
        with col2:
            age = st.number_input("年龄", min_value=6, max_value=18, value=12)
            grade = st.selectbox("年级", ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级", 
                                      "七年级", "八年级", "九年级", "高一", "高二", "高三"])

    school = st.text_input("学校", placeholder="请输入学校名称")

    # 开始测评按钮
    if st.button("🚀 开始创造力测评", type="primary", disabled=not all([student_name, student_id, school])):
        if not all([student_name, student_id, school]):
            st.error("请填写完整的学生信息")
            return
        _app_log.info("start_assessment clicked: id=%s name=%s", student_id, student_name)
        # 创建学生档案
        student_profile = StudentProfile(
            student_id=student_id,
            name=student_name,
            age=age,
            grade=grade,
            school=school,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 保存学生档案
        if components["db"].create_student_profile(student_profile):
            st.success("学生档案创建成功！")
        else:
            st.warning("学生档案已存在，将使用现有档案")

        # 开始测评
        start_assessment(student_profile)

def start_assessment(student_profile: StudentProfile):
    """开始测评流程"""
    st.session_state.assessment_in_progress = True
    st.session_state.student_profile = student_profile
    st.session_state.current_question = 0
    st.session_state.answers = []
    st.session_state.evaluations = []  # 累计每题评分
    st.session_state.start_time = datetime.now()
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 生成题目
    with st.spinner("正在生成测评题目..."):
        questions = components["graph"].create_questions(Config.MAX_QUESTIONS)

    st.session_state.questions = questions

    # 显示测评界面
    display_assessment_interface()

def display_assessment_interface():
    """显示测评界面"""
    if not st.session_state.get("assessment_in_progress", False):
        return
    
    questions = st.session_state.questions
    current_q = st.session_state.current_question
    
    if current_q >= len(questions):
        # 测评完成
        complete_assessment()
        return
    
    question = questions[current_q]
    
    # 显示题目
    st.subheader(f"题目 {current_q + 1}/{len(questions)}")
    st.markdown(f"**{question.title}**")
    st.markdown(f"**题目内容：** {question.content}")
    
    # 显示测评维度
    dimensions = [Config.CREATIVITY_DIMENSIONS.get(d.value, d.value) for d in question.dimensions]
    st.info(f"测评维度：{', '.join(dimensions)}")
    
    # 答案输入与确认（表单提交，替代 Ctrl+Enter）
    answer_key = f"answer_input_{question.id}"
    confirm_flag_key = f"confirmed_{question.id}"
    confirmed_answer_key = f"confirmed_answer_{question.id}"

    with st.form(f"answer_form_{question.id}", clear_on_submit=False):
        answer = st.text_area(
            "请输入您的答案：",
            height=200,
            placeholder="请在此输入您的创造性回答...",
            key=answer_key
        )
        submitted = st.form_submit_button("✅ 确认答案")
        if submitted:
            if answer.strip():
                st.session_state[confirm_flag_key] = True
                st.session_state[confirmed_answer_key] = answer
                st.success("已确认当前答案")
            else:
                st.warning("请输入内容后再确认")

    # 如答案与已确认内容不一致，自动取消确认
    if st.session_state.get(confirm_flag_key, False):
        if st.session_state.get(confirmed_answer_key, "") != st.session_state.get(answer_key, ""):
            st.session_state[confirm_flag_key] = False

    col_next, col_end = st.columns([1, 3])
    with col_next:
        next_disabled = not st.session_state.get(confirm_flag_key, False)
        if st.button("⏭️ 下一题", disabled=next_disabled):
            final_answer = st.session_state.get(confirmed_answer_key, "").strip()
            if not final_answer:
                st.warning("请先输入并确认答案")
            else:
                # 保存答案
                save_answer(question, final_answer)
                # 评分并累计
                with st.spinner("正在评分..."):
                    scores = components["graph"].score_answer(question.content, final_answer)
                _app_log.info("score_done: qid=%s scores=%s", question.id, scores)
                st.session_state.evaluations.append({
                    "question_id": question.id,
                    "scores": scores,
                    "timestamp": datetime.now(),
                })
                st.session_state.current_question += 1
                st.rerun()
    with col_end:
        if st.button("⏹️ 结束测评"):
            if st.session_state.answers:
                complete_assessment()
            else:
                st.warning("请至少完成一题再结束测评")

def save_answer(question, answer_text):
    """保存学生答案"""
    answer = {
        "question_id": question.id,
        "content": answer_text,
        "timestamp": datetime.now(),
        "time_spent": 0  # 简化处理
    }
    _app_log.info("save_answer: qid=%s length=%d", question.id, len(answer_text or ""))
    st.session_state.answers.append(answer)

def complete_assessment():
    """完成测评"""
    st.session_state.assessment_in_progress = False
    
    # 生成测评结果（基于累计评分）
    questions = st.session_state.questions
    evaluations = st.session_state.evaluations
    student_profile = st.session_state.student_profile

    # 汇总各维度平均分
    totals = {d.value: 0.0 for d in CreativityDimension}
    n = max(1, len(evaluations))
    for ev in evaluations:
        s = ev["scores"]
        for d in totals:
            totals[d] += float(s.get(d, 0))
    for d in totals:
        totals[d] /= n

    # 转为 CreativityScore 列表
    dimension_scores = []
    for dimension in CreativityDimension:
        score = float(totals[dimension.value])
        dimension_scores.append(CreativityScore(
            dimension=dimension,
            score=score,
            max_score=10.0,
            percentage=score * 10
        ))

    total_score = sum(s.score for s in dimension_scores)
    overall_level = "优秀" if total_score >= 35 else "良好" if total_score >= 30 else "一般"

    assessment_result = AssessmentResult(
        session_id=st.session_state.session_id,
        student_id=student_profile.student_id,
        student_name=student_profile.name,
        total_score=total_score,
        dimension_scores=dimension_scores,
        overall_level=overall_level,
        recommendations=["继续努力，保持创新思维！"],
        completed_at=datetime.now()
    )

    # 保存结果
    components["db"].save_assessment_result(assessment_result)
    _app_log.info("complete_assessment: session=%s total=%.2f", st.session_state.session_id, total_score)

    # 显示结果
    st.success("🎉 测评完成！")
    display_assessment_results(assessment_result)

def display_assessment_results(result: AssessmentResult):
    """显示测评结果"""
    st.header("📊 测评结果")
    
    # 总体得分
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总分", f"{result.total_score:.1f}/40.0")
    with col2:
        st.metric("等级", result.overall_level)
    with col3:
        st.metric("完成时间", result.completed_at.strftime("%Y-%m-%d %H:%M"))
    
    # 各维度得分
    st.subheader("各维度得分")
    
    dimension_data = []
    for score in result.dimension_scores:
        dimension_data.append({
            "维度": Config.CREATIVITY_DIMENSIONS.get(score.dimension.value, score.dimension.value),
            "得分": score.score,
            "百分比": f"{score.percentage:.1f}%"
        })
    
    df = pd.DataFrame(dimension_data)
    st.dataframe(df, width='stretch')
    
    # 可视化图表
    col1, col2 = st.columns(2)
    
    with col1:
        # 雷达图
        fig_radar = components["analyzer"].generate_radar_chart(result)
        st.plotly_chart(fig_radar, width='stretch')
    
    with col2:
        # 柱状图
        fig_bar = components["analyzer"].generate_bar_chart(result)
        st.plotly_chart(fig_bar, width='stretch')
    
    # 建议
    st.subheader("💡 改进建议")
    for i, rec in enumerate(result.recommendations, 1):
        st.write(f"{i}. {rec}")

def result_analysis_page():
    """结果分析页面"""
    st.header("📈 测评结果分析")
    
    # 选择学生
    all_results = components["db"].get_all_assessment_results()
    if not all_results:
        st.info("暂无测评结果数据")
        return
    
    student_names = list(set(r.student_name for r in all_results))
    selected_student = st.selectbox("选择学生", student_names)
    
    if selected_student:
        # 获取该学生的所有测评结果（时间倒序）
        student_results = [r for r in all_results if r.student_name == selected_student]
        if not student_results:
            st.info("该学生暂无测评结果")
            return
        sorted_results = sorted(student_results, key=lambda x: x.completed_at, reverse=True)

        # 选择某一次测评
        attempt_labels = [f"{i+1}. {res.completed_at.strftime('%Y-%m-%d %H:%M')} | 总分 {res.total_score:.1f}" for i, res in enumerate(sorted_results)]
        selected_idx = st.selectbox("选择一次测评结果", list(range(len(sorted_results))), format_func=lambda i: attempt_labels[i])

        # 显示该次结果详情
        display_single_result_analysis(sorted_results[selected_idx])

        # 历史趋势（如至少两次）
        if len(sorted_results) >= 2:
            st.subheader("📉 历史趋势")
            fig_trend = components["analyzer"].generate_trend_analysis(sorted(sorted_results, key=lambda x: x.completed_at))
            if fig_trend:
                st.plotly_chart(fig_trend, width='stretch')

def display_single_result_analysis(result: AssessmentResult):
    """显示单次测评结果分析"""
    st.subheader(f"{result.student_name} 的测评结果分析")
    
    # 基本分析
    analysis = components["analyzer"].analyze_single_result(result)
    
    # 总体表现
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总分", f"{analysis['overall_scores']['total_score']:.1f}")
    with col2:
        st.metric("百分比", f"{analysis['overall_scores']['percentage']:.1f}%")
    with col3:
        st.metric("等级", analysis['overall_scores']['level'])
    with col4:
        st.metric("完成时间", result.completed_at.strftime("%m-%d %H:%M"))
    
    # 各维度详细分析
    st.subheader("各维度详细分析")
    
    dimension_analysis = analysis['dimension_analysis']
    for dim_name, dim_data in dimension_analysis.items():
        with st.expander(f"{dim_name} - {dim_data['level']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("得分", f"{dim_data['score']:.1f}")
            with col2:
                st.metric("满分", f"{dim_data['max_score']:.1f}")
            with col3:
                st.metric("百分比", f"{dim_data['percentage']:.1f}%")
    
    # 可视化
    col1, col2 = st.columns(2)
    with col1:
        fig_radar = components["analyzer"].generate_radar_chart(result)
        st.plotly_chart(fig_radar, width='stretch')
    
    with col2:
        fig_bar = components["analyzer"].generate_bar_chart(result)
        st.plotly_chart(fig_bar, width='stretch')

def display_trend_analysis(results: List[AssessmentResult]):
    """显示趋势分析"""
    st.subheader(f"{results[0].student_name} 的测评趋势分析")
    
    # 按时间排序
    sorted_results = sorted(results, key=lambda x: x.completed_at)
    
    # 趋势数据
    dates = [r.completed_at.strftime('%Y-%m-%d') for r in sorted_results]
    total_scores = [r.total_score for r in sorted_results]
    
    # 总分趋势
    fig_total = go.Figure()
    fig_total.add_trace(go.Scatter(
        x=dates,
        y=total_scores,
        mode='lines+markers',
        name='总分',
        line=dict(width=3, color='#32C997')
    ))
    
    fig_total.update_layout(
        title="总分发展趋势",
        xaxis_title="测评时间",
        yaxis_title="总分",
        height=400
    )
    
    st.plotly_chart(fig_total, width='stretch')
    
    # 各维度趋势
    if len(sorted_results) >= 2:
        fig_trend = components["analyzer"].generate_trend_analysis(sorted_results)
        if fig_trend:
            st.plotly_chart(fig_trend, width='stretch')

def student_management_page():
    """学生管理页面"""
    st.header("👥 学生管理")
    
    # 学生列表
    all_results = components["db"].get_all_assessment_results()
    if all_results:
        # 创建学生统计表
        student_stats = {}
        for result in all_results:
            if result.student_name not in student_stats:
                student_stats[result.student_name] = {
                    "student_id": result.student_id,
                    "total_assessments": 0,
                    "latest_score": 0,
                    "latest_date": None,
                    "best_score": 0
                }
            
            student_stats[result.student_name]["total_assessments"] += 1
            if (student_stats[result.student_name]["latest_date"] is None or 
                result.completed_at > student_stats[result.student_name]["latest_date"]):
                student_stats[result.student_name]["latest_score"] = result.total_score
                student_stats[result.student_name]["latest_date"] = result.completed_at
            
            if result.total_score > student_stats[result.student_name]["best_score"]:
                student_stats[result.student_name]["best_score"] = result.total_score
        
        # 显示统计表
        stats_data = []
        for name, stats in student_stats.items():
            stats_data.append({
                "姓名": name,
                "学号": stats["student_id"],
                "测评次数": stats["total_assessments"],
                "最新得分": f"{stats['latest_score']:.1f}",
                "最高得分": f"{stats['best_score']:.1f}",
                "最新测评": stats["latest_date"].strftime("%Y-%m-%d") if stats["latest_date"] else "无"
            })
        
        df = pd.DataFrame(stats_data)
        st.dataframe(df, width='stretch')
        
        # 下载数据
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载学生数据",
            data=csv,
            file_name=f"学生测评数据_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("暂无学生数据")

def system_settings_page():
    """系统设置页面"""
    st.header("⚙️ 系统设置")
    
    st.subheader("测评配置")
    
    col1, col2 = st.columns(2)
    with col1:
        # 允许最小为1题，并对默认值做边界处理，避免低于最小值时报错
        default_max_q = max(1, min(20, Config.MAX_QUESTIONS))
        max_questions = st.number_input("最大题目数量", min_value=1, max_value=20, value=default_max_q)
        time_limit = st.number_input("时间限制（分钟）", min_value=10, max_value=60, value=Config.TIME_LIMIT_MINUTES)
    
    with col2:
        st.info(f"当前配置：\n- 最大题目数：{Config.MAX_QUESTIONS}\n- 时间限制：{Config.TIME_LIMIT_MINUTES}分钟")
    
    st.subheader("系统信息")
    st.text(f"应用名称：{Config.APP_NAME}")
    st.text(f"数据库：{Config.DATABASE_URL}")
    st.text(f"调试模式：{Config.DEBUG}")
    
    # 数据统计
    all_results = components["db"].get_all_assessment_results()
    st.subheader("数据统计")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总测评次数", len(all_results))
    with col2:
        unique_students = len(set(r.student_name for r in all_results))
        st.metric("参与学生数", unique_students)
    with col3:
        if all_results:
            avg_score = sum(r.total_score for r in all_results) / len(all_results)
            st.metric("平均得分", f"{avg_score:.1f}")
        else:
            st.metric("平均得分", "0.0")

if __name__ == "__main__":
    main()
