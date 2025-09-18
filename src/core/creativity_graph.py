"""
基于LangGraph的创造力测评工作流
"""
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.data.models import Question, Answer, AssessmentSession, QuestionType, CreativityDimension
from src.core.config import Config
from src.core.question_bank import ensure_question_files, sample_questions_per_type
from src.core.logging_utils import get_app_logger, get_llm_logger

class GraphState(TypedDict):
    """LangGraph状态定义"""
    session_id: str
    student_id: str
    student_name: str
    current_question_index: int
    questions: List[Question]
    answers: List[Answer]
    session_data: Dict[str, Any]
    next_action: str

class CreativityAssessmentGraph:
    """创造力测评LangGraph工作流"""
    
    def __init__(self):
        self.app_log = get_app_logger("creativity_graph")
        self.llm_log = get_llm_logger("creativity_graph.llm")
        self.llm = ChatOpenAI(
        openai_api_key=Config.api_key,  # 使用硅基流动的Key
        model=Config.model_name_a,       # 如 "DeepSeek-V3"
        base_url=Config.base_url,
        temperature=0,
        timeout=15,
        max_retries=0,
        )
        # 为并行Agent准备两套客户端（可设置轻微温度差异以增加多样性）
        self.llm_a = self.llm
        self.llm_b = ChatOpenAI(
        openai_api_key=Config.api_key,
        model=Config.model_name_b,
        base_url=Config.base_url,
        temperature=0.3,
        timeout=15,
        max_retries=0,
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建LangGraph工作流"""
        workflow = StateGraph(GraphState)
        
        # 添加节点
        workflow.add_node("initialize_session", self._initialize_session)
        workflow.add_node("generate_questions", self._generate_questions)
        workflow.add_node("present_question", self._present_question)
        workflow.add_node("collect_answer", self._collect_answer)
        workflow.add_node("evaluate_answer", self._evaluate_answer)
        workflow.add_node("generate_next_question", self._generate_next_question)
        workflow.add_node("finalize_assessment", self._finalize_assessment)
        
        # 设置入口点
        workflow.set_entry_point("initialize_session")
        
        # 添加边
        workflow.add_edge("initialize_session", "generate_questions")
        workflow.add_edge("generate_questions", "present_question")
        workflow.add_edge("present_question", "collect_answer")
        workflow.add_edge("collect_answer", "evaluate_answer")
        workflow.add_edge("evaluate_answer", "generate_next_question")
        workflow.add_edge("finalize_assessment", END)
        
        # 添加条件边
        workflow.add_conditional_edges(
            "generate_next_question",
            self._should_continue,
            {
                "continue": "present_question",
                "finish": "finalize_assessment"
            }
        )
        
        return workflow.compile()
    
    def _initialize_session(self, state: GraphState) -> GraphState:
        """初始化测评会话"""
        print(f"初始化测评会话: {state['student_name']}")
        
        state["current_question_index"] = 0
        state["questions"] = []
        state["answers"] = []
        state["session_data"] = {
            "start_time": datetime.now().isoformat(),
            "total_questions": Config.MAX_QUESTIONS,
            "evaluations": []
        }
        state["next_action"] = "generate_questions"
        
        return state
    
    def _generate_questions(self, state: GraphState) -> GraphState:
        """生成测评题目"""
        print("生成创造力测评题目...")
        
        # 生成不同类型的题目
        questions = []
        question_types = list(QuestionType)
        
        for i in range(Config.MAX_QUESTIONS):
            question_type = random.choice(question_types)
            question = self._create_question(i, question_type)
            questions.append(question)
        
        state["questions"] = questions
        state["next_action"] = "present_question"
        
        return state
    
    def _create_question(self, index: int, question_type: QuestionType) -> Question:
        """创建单个题目"""
        question_templates = {
            QuestionType.DIVERGENT_THINKING: {
                "title": f"发散思维题 {index + 1}",
                "content": "请尽可能多地列举出{主题}的用途。至少写出10个不同的用途。",
                "dimensions": [CreativityDimension.FLUENCY, CreativityDimension.FLEXIBILITY]
            },
            QuestionType.CONVERGENT_THINKING: {
                "title": f"聚合思维题 {index + 1}",
                "content": "请找出以下物品的共同点：{物品列表}。至少找出5个共同特征。",
                "dimensions": [CreativityDimension.FLEXIBILITY, CreativityDimension.ORIGINALITY]
            },
            QuestionType.CREATIVE_PROBLEM_SOLVING: {
                "title": f"创造性问题解决 {index + 1}",
                "content": "请设计一个创新的解决方案来解决以下问题：{问题描述}。",
                "dimensions": [CreativityDimension.ORIGINALITY, CreativityDimension.ELABORATION]
            },
            QuestionType.IMAGINATION: {
                "title": f"想象力测试 {index + 1}",
                "content": "请描述一个想象中的{场景}，要求具有创新性和独特性。",
                "dimensions": [CreativityDimension.ORIGINALITY, CreativityDimension.ELABORATION]
            }
        }
        
        template = question_templates[question_type]
        themes = ["砖头", "回形针", "报纸", "雨伞", "橡皮筋"]
        items = ["苹果、橙子、香蕉", "汽车、飞机、轮船", "书、电脑、手机"]
        problems = ["如何让城市更环保", "如何提高学习效率", "如何减少交通拥堵"]
        scenes = ["未来学校", "外星球", "海底城市"]
        
        content = template["content"].format(
            主题=random.choice(themes),
            物品列表=random.choice(items),
            问题描述=random.choice(problems),
            场景=random.choice(scenes)
        )
        
        return Question(
            id=f"q_{index}",
            type=question_type,
            title=template["title"],
            content=content,
            time_limit=300,
            dimensions=template["dimensions"],
            scoring_criteria={
                "fluency_weight": 0.3,
                "flexibility_weight": 0.3,
                "originality_weight": 0.2,
                "elaboration_weight": 0.2
            }
        )
    
    def _present_question(self, state: GraphState) -> GraphState:
        """展示当前题目"""
        current_index = state["current_question_index"]
        question = state["questions"][current_index]
        
        print(f"\n=== {question.title} ===")
        print(f"题目内容: {question.content}")
        print(f"时间限制: {question.time_limit}秒")
        print(f"测评维度: {[d.value for d in question.dimensions]}")
        
        state["next_action"] = "collect_answer"
        return state
    
    def _collect_answer(self, state: GraphState) -> GraphState:
        """收集学生答案"""
        # 在实际应用中，这里会通过Web界面收集答案
        # 这里模拟收集答案的过程
        current_index = state["current_question_index"]
        question = state["questions"][current_index]
        
        # 模拟学生答案（实际应用中从用户输入获取）
        mock_answer = f"这是学生对题目 {question.id} 的回答内容..."
        
        answer = Answer(
            question_id=question.id,
            student_id=state["student_id"],
            content=mock_answer,
            timestamp=datetime.now(),
            time_spent=random.randint(60, 300)
        )
        
        state["answers"].append(answer)
        state["next_action"] = "evaluate_answer"
        
        return state
    
    def _evaluate_answer(self, state: GraphState) -> GraphState:
        """评估学生答案"""
        current_index = state["current_question_index"]
        question = state["questions"][current_index]
        answer = state["answers"][-1]
        
        print(f"正在评估答案: {answer.question_id}")
        
        # 使用LLM评估答案的创造力维度
        evaluation_prompt = (
            "请评估以下学生答案的创造力水平，从四个维度进行评分（0-10分）：\n\n"
            f"题目: {question.content}\n"
            f"学生答案: {answer.content}\n\n"
            "请从以下维度评分：\n"
            "1. 流畅性 (Fluency): 答案的数量和丰富程度\n"
            "2. 灵活性 (Flexibility): 答案的多样性和变化性\n"
            "3. 独创性 (Originality): 答案的独特性和创新性\n"
            "4. 精细性 (Elaboration): 答案的详细程度和深度\n\n"
            "请以JSON格式返回评分结果：\n"
            "{\n"
            "    \"fluency\": 分数,\n"
            "    \"flexibility\": 分数,\n"
            "    \"originality\": 分数,\n"
            "    \"elaboration\": 分数,\n"
            "    \"comments\": \"评价意见\"\n"
            "}\n"
            "重要要求：仅输出上述JSON对象本身，不要包含任何多余文字、解释或代码块标记。\n"
        )
        
        try:
            response = self.llm.invoke([HumanMessage(content=evaluation_prompt)])
            raw = getattr(response, "content", "") or ""
            print("LLM原始返回：", raw)
            # 解析模型返回，兼容带说明文字/代码块
            text = raw.strip()
            if text.startswith("```"):
                # 去掉反引号包裹
                text = text.strip("`")
                # 去掉可能的json语言标记
                if text.lower().startswith("json\n"):
                    text = text[5:]
            import re, json as _json
            match = re.search(r"\{[\s\S]*\}", text)
            json_str = match.group(0) if match else text
            evaluation = _json.loads(json_str)
            
            # 存储评估结果
            if "evaluations" not in state["session_data"]:
                state["session_data"]["evaluations"] = []
            
            state["session_data"]["evaluations"].append({
                "question_id": question.id,
                "scores": evaluation,
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"评估完成: {evaluation}")
            
        except Exception as e:
            print(f"评估过程中出现错误: {e}")
            try:
                print("LLM原始返回：", raw[:1000])
            except Exception:
                pass
            # 使用默认评分
            state["session_data"]["evaluations"].append({
                "question_id": question.id,
                "scores": {
                    "fluency": 7.0,
                    "flexibility": 7.0,
                    "originality": 7.0,
                    "elaboration": 7.0,
                    "comments": "自动评分"
                },
                "timestamp": datetime.now().isoformat()
            })
        
        state["next_action"] = "generate_next_question"
        return state
    
    def _generate_next_question(self, state: GraphState) -> GraphState:
        """生成下一题或结束测评"""
        state["current_question_index"] += 1
        state["next_action"] = "present_question"
        return state
    
    def _should_continue(self, state: GraphState) -> str:
        """判断是否继续测评"""
        current_index = state["current_question_index"]
        total_questions = len(state["questions"])
        
        if current_index < total_questions:
            return "continue"
        else:
            return "finish"
    
    def _finalize_assessment(self, state: GraphState) -> GraphState:
        """完成测评并生成结果"""
        print("正在生成最终测评结果...")
        
        # 计算各维度总分
        evaluations = state["session_data"].get("evaluations", [])
        dimension_totals = {
            "fluency": 0,
            "flexibility": 0,
            "originality": 0,
            "elaboration": 0
        }
        
        for eval_data in evaluations:
            scores = eval_data["scores"]
            for dimension in dimension_totals:
                dimension_totals[dimension] += scores.get(dimension, 0)
        
        # 计算平均分
        num_questions = len(evaluations)
        if num_questions > 0:
            for dimension in dimension_totals:
                dimension_totals[dimension] /= num_questions
        
        # 存储最终结果
        state["session_data"]["final_results"] = {
            "dimension_scores": dimension_totals,
            "total_score": sum(dimension_totals.values()),
            "completed_at": datetime.now().isoformat()
        }
        
        print(f"测评完成! 总分: {state['session_data']['final_results']['total_score']:.2f}")
        print(f"各维度得分: {dimension_totals}")
        
        state["next_action"] = "completed"
        return state
    
    def run_assessment(self, student_id: str, student_name: str) -> Dict[str, Any]:
        """运行完整的创造力测评"""
        initial_state = GraphState(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            student_id=student_id,
            student_name=student_name,
            current_question_index=0,
            questions=[],
            answers=[],
            session_data={},
            next_action=""
        )
        
        result = self.graph.invoke(initial_state)
        return result

    def create_questions(self, num_questions: int) -> List[Question]:
        """对外暴露：从题库抽取指定数量的题目"""
        ensure_question_files()
        sampled = sample_questions_per_type(num_questions)
        questions: List[Question] = []
        for idx, q in enumerate(sampled):
            questions.append(Question(
                id=q.get("id", f"q_{idx}"),
                type=QuestionType(q["type"]),
                title=q["title"],
                content=q["content"],
                time_limit=int(q.get("time_limit", 300)),
                dimensions=[CreativityDimension(d) for d in q.get("dimensions", [])],
                scoring_criteria=q.get("scoring_criteria", {})
            ))
        return questions

    def _build_evaluation_prompt(self, role_hint: str, question_content: str, answer_text: str) -> str:
        prompt = (
            f"你是{role_hint}。请评估以下学生答案的创造力水平，从四个维度进行评分（0-10分）：\n\n"
            f"题目: {question_content}\n"
            f"学生答案: {answer_text}\n\n"
            "请从以下维度评分：\n"
            "1. 流畅性 (Fluency): 答案的数量和丰富程度\n"
            "2. 灵活性 (Flexibility): 答案的多样性和变化性\n"
            "3. 独创性 (Originality): 答案的独特性和创新性\n"
            "4. 精细性 (Elaboration): 答案的详细程度和深度\n\n"
            "请以JSON格式返回评分结果：\n"
            "{\n"
            "    \"fluency\": 分数,\n"
            "    \"flexibility\": 分数,\n"
            "    \"originality\": 分数,\n"
            "    \"elaboration\": 分数,\n"
            "    \"comments\": \"评价意见\"\n"
            "}\n"
            "重要要求：仅输出上述JSON对象本身，不要包含任何多余文字、解释或代码块标记。\n"
        )
        return prompt

    def _parse_evaluation_text(self, raw: str) -> Dict[str, Any]:
        text = (raw or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json\n"):
                text = text[5:]
        import re, json as _json
        match = re.search(r"\{[\s\S]*\}", text)
        json_str = match.group(0) if match else text
        data = _json.loads(json_str)
        return data

    def score_answer(self, question_content: str, answer_text: str) -> Dict[str, Any]:
        """对给定题目与用户答案进行并行双Agent评分并取平均。"""
        prompt_a = self._build_evaluation_prompt("严谨的评分者，偏保守且注重细节", question_content, answer_text)
        prompt_b = self._build_evaluation_prompt("发散的评分者，鼓励创造性表达与多样性", question_content, answer_text)
        self.llm_log.info("Prompt A:\n%s", prompt_a)
        self.llm_log.info("Prompt B:\n%s", prompt_b)

        def call(tag: str, llm_client, prompt):
            try:
                resp = llm_client.invoke([HumanMessage(content=prompt)])
                raw = getattr(resp, "content", "") or ""
                self.llm_log.info("%s Raw:\n%s", tag, raw)
                parsed = self._parse_evaluation_text(raw)
                self.llm_log.info("%s Parsed: %s", tag, parsed)
                return parsed
            except Exception as e:
                self.llm_log.exception("%s Error: %s", tag, e)
                return None

        with ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(call, "AgentA", self.llm_a, prompt_a)
            f2 = ex.submit(call, "AgentB", self.llm_b, prompt_b)
            r1 = f1.result()
            r2 = f2.result()

        # 回退策略
        defaults = {"fluency": 7.0, "flexibility": 7.0, "originality": 7.0, "elaboration": 7.0}
        if r1 is None and r2 is None:
            self.app_log.warning("Both agents failed, using defaults")
            return {**defaults, "comments": "自动评分（双Agent均失败）"}
        if r1 is None:
            return {
                "fluency": float(r2.get("fluency", 7.0)),
                "flexibility": float(r2.get("flexibility", 7.0)),
                "originality": float(r2.get("originality", 7.0)),
                "elaboration": float(r2.get("elaboration", 7.0)),
                "comments": f"B: {r2.get('comments', '')}"
            }
        if r2 is None:
            return {
                "fluency": float(r1.get("fluency", 7.0)),
                "flexibility": float(r1.get("flexibility", 7.0)),
                "originality": float(r1.get("originality", 7.0)),
                "elaboration": float(r1.get("elaboration", 7.0)),
                "comments": f"A: {r1.get('comments', '')}"
            }

        # 平均两者分数
        avg = {}
        for k in ("fluency", "flexibility", "originality", "elaboration"):
            v1 = float(r1.get(k, 7.0))
            v2 = float(r2.get(k, 7.0))
            avg[k] = (v1 + v2) / 2.0
        avg["comments"] = f"A: {r1.get('comments', '')} | B: {r2.get('comments', '')}"
        return avg
