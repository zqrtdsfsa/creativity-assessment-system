"""
创造力测评结果分析和可视化模块
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any
import json
from datetime import datetime

from src.data.models import AssessmentResult, CreativityScore, CreativityDimension
from src.core.config import Config

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class CreativityAnalyzer:
    """创造力测评结果分析器"""
    
    def __init__(self):
        self.dimensions = Config.CREATIVITY_DIMENSIONS
    
    def analyze_single_result(self, result: AssessmentResult) -> Dict[str, Any]:
        """分析单个测评结果"""
        analysis = {
            "student_info": {
                "name": result.student_name,
                "student_id": result.student_id,
                "completed_at": result.completed_at
            },
            "overall_scores": {
                "total_score": result.total_score,
                "max_possible_score": 40.0,  # 假设每维度最高10分
                "percentage": (result.total_score / 40.0) * 100,
                "level": result.overall_level
            },
            "dimension_analysis": {}
        }
        
        # 分析各维度得分
        for score in result.dimension_scores:
            dimension_name = self.dimensions.get(score.dimension.value, score.dimension.value)
            analysis["dimension_analysis"][dimension_name] = {
                "score": score.score,
                "max_score": score.max_score,
                "percentage": score.percentage,
                "level": self._get_dimension_level(score.percentage)
            }
        
        return analysis
    
    def _get_dimension_level(self, percentage: float) -> str:
        """根据百分比确定维度水平"""
        if percentage >= 90:
            return "优秀"
        elif percentage >= 80:
            return "良好"
        elif percentage >= 70:
            return "一般"
        else:
            return "需要提升"
    
    def compare_with_peers(self, student_result: AssessmentResult, 
                          peer_results: List[AssessmentResult]) -> Dict[str, Any]:
        """与同龄人比较分析"""
        if not peer_results:
            return {"error": "没有可比较的同龄人数据"}
        
        # 计算同龄人平均分
        peer_dimensions = {dim: [] for dim in self.dimensions.keys()}
        peer_total_scores = []
        
        for result in peer_results:
            peer_total_scores.append(result.total_score)
            for score in result.dimension_scores:
                peer_dimensions[score.dimension.value].append(score.score)
        
        comparison = {
            "total_score_comparison": {
                "student_score": student_result.total_score,
                "peer_average": sum(peer_total_scores) / len(peer_total_scores),
                "peer_median": sorted(peer_total_scores)[len(peer_total_scores) // 2],
                "percentile": self._calculate_percentile(student_result.total_score, peer_total_scores)
            },
            "dimension_comparison": {}
        }
        
        # 各维度比较
        for dimension, scores in peer_dimensions.items():
            if scores:
                dimension_name = self.dimensions.get(dimension, dimension)
                student_dimension_score = next(
                    (s.score for s in student_result.dimension_scores 
                     if s.dimension.value == dimension), 0
                )
                
                comparison["dimension_comparison"][dimension_name] = {
                    "student_score": student_dimension_score,
                    "peer_average": sum(scores) / len(scores),
                    "peer_median": sorted(scores)[len(scores) // 2],
                    "percentile": self._calculate_percentile(student_dimension_score, scores)
                }
        
        return comparison
    
    def _calculate_percentile(self, score: float, scores: List[float]) -> float:
        """计算百分位数"""
        sorted_scores = sorted(scores)
        count_below = sum(1 for s in sorted_scores if s < score)
        return (count_below / len(sorted_scores)) * 100
    
    def generate_radar_chart(self, result: AssessmentResult) -> go.Figure:
        """生成雷达图"""
        categories = list(self.dimensions.values())  # 未闭合的类别，用于坐标轴
        scores = []
        
        for dim_key in self.dimensions.keys():
            score = next(
                (s.score for s in result.dimension_scores 
                 if s.dimension.value == dim_key), 0
            )
            scores.append(score)
        
        # 绘图时闭合
        theta_closed = categories + [categories[0]]
        scores_closed = scores + [scores[0]]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores_closed,
            theta=theta_closed,
            fill='toself',
            name=result.student_name,
            line_color='rgb(32, 201, 151)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                ),
                angularaxis=dict(
                    direction="clockwise",
                    tickfont=dict(size=11),
                    categoryorder="array",
                    categoryarray=categories,
                    tickmode="array",
                    tickvals=categories,
                    ticktext=categories,
                    rotation=0
                )
            ),
            showlegend=True,
            title=f"{result.student_name} 创造力测评雷达图",
            font=dict(size=12),
            margin=dict(l=90, r=90, t=80, b=90),  # 增大边距避免中文被裁切
            height=520
        )
        
        return fig
    
    def generate_bar_chart(self, result: AssessmentResult) -> go.Figure:
        """生成柱状图"""
        dimensions = []
        scores = []
        colors = []
        
        for score in result.dimension_scores:
            dimensions.append(self.dimensions.get(score.dimension.value, score.dimension.value))
            scores.append(score.score)
            
            # 根据分数设置颜色
            if score.percentage >= 90:
                colors.append('#2E8B57')  # 深绿色
            elif score.percentage >= 80:
                colors.append('#32C997')  # 绿色
            elif score.percentage >= 70:
                colors.append('#FFD700')  # 金色
            else:
                colors.append('#FF6B6B')  # 红色
        
        fig = go.Figure(data=[
            go.Bar(
                x=dimensions,
                y=scores,
                marker_color=colors,
                text=[f"{s:.1f}" for s in scores],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title=f"{result.student_name} 各维度得分柱状图",
            xaxis_title="创造力维度",
            yaxis_title="得分",
            yaxis=dict(range=[0, 10]),
            font=dict(size=12)
        )
        
        return fig
    
    def generate_trend_analysis(self, student_results: List[AssessmentResult]) -> go.Figure:
        """生成趋势分析图（横坐标为测评次数，均匀分布）"""
        if len(student_results) < 2:
            return None
        
        # 按时间排序
        sorted_results = sorted(student_results, key=lambda x: x.completed_at)
        
        # 使用均匀的测评次数作为横坐标，保留日期用于悬浮提示
        attempts = list(range(1, len(sorted_results) + 1))
        dates = [r.completed_at.strftime('%Y-%m-%d %H:%M') for r in sorted_results]
        total_scores = [r.total_score for r in sorted_results]
        
        # 各维度趋势
        dimension_trends = {dim: [] for dim in self.dimensions.keys()}
        
        for result in sorted_results:
            for score in result.dimension_scores:
                dimension_trends[score.dimension.value].append(score.score)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=list(self.dimensions.values()),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        for i, (dim, scores) in enumerate(dimension_trends.items()):
            if i < len(positions):
                fig.add_trace(
                    go.Scatter(
                        x=attempts,
                        y=scores,
                        mode='lines+markers',
                        name=self.dimensions.get(dim, dim),
                        line=dict(width=3),
                        hovertext=dates,
                        hovertemplate='第%{x}次<br>日期：%{hovertext}<br>分数：%{y:.1f}<extra></extra>'
                    ),
                    row=positions[i][0],
                    col=positions[i][1]
                )
        
        fig.update_layout(
            title=f"{sorted_results[0].student_name} 创造力发展趋势（按测评次数）",
            height=600,
            showlegend=False,
            xaxis_title_text='测评次数'
        )
        
        # 设置各子图的x轴标题
        fig.update_xaxes(title_text="测评次数", row=1, col=1)
        fig.update_xaxes(title_text="测评次数", row=1, col=2)
        fig.update_xaxes(title_text="测评次数", row=2, col=1)
        fig.update_xaxes(title_text="测评次数", row=2, col=2)
        
        return fig
    
    def generate_comprehensive_report(self, result: AssessmentResult, 
                                    peer_results: List[AssessmentResult] = None) -> Dict[str, Any]:
        """生成综合报告"""
        report = {
            "basic_analysis": self.analyze_single_result(result),
            "charts": {
                "radar_chart": self.generate_radar_chart(result),
                "bar_chart": self.generate_bar_chart(result)
            },
            "recommendations": self._generate_recommendations(result),
            "timestamp": datetime.now().isoformat()
        }
        
        if peer_results:
            report["peer_comparison"] = self.compare_with_peers(result, peer_results)
        
        return report
    
    def _generate_recommendations(self, result: AssessmentResult) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for score in result.dimension_scores:
            dimension_name = self.dimensions.get(score.dimension.value, score.dimension.value)
            
            if score.percentage < 70:
                if score.dimension == CreativityDimension.FLUENCY:
                    recommendations.append(f"建议通过头脑风暴练习提高{dimension_name}，多进行发散思维训练")
                elif score.dimension == CreativityDimension.FLEXIBILITY:
                    recommendations.append(f"建议尝试从不同角度思考问题，提高{dimension_name}")
                elif score.dimension == CreativityDimension.ORIGINALITY:
                    recommendations.append(f"建议培养创新思维，敢于提出独特想法，提高{dimension_name}")
                elif score.dimension == CreativityDimension.ELABORATION:
                    recommendations.append(f"建议在思考时更加深入细致，提高{dimension_name}")
        
        if not recommendations:
            recommendations.append("恭喜！您的创造力水平表现优秀，继续保持！")
        
        return recommendations
