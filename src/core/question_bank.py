import os
import json
import random
from typing import Dict, List
from datetime import datetime

from src.data.models import CreativityDimension, QuestionType

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS_DIR = os.path.join(BASE_DIR, "..", "questions")
QUESTIONS_DIR = os.path.abspath(QUESTIONS_DIR)

FILE_MAP = {
    QuestionType.DIVERGENT_THINKING.value: "divergent_thinking.json",
    QuestionType.CONVERGENT_THINKING.value: "convergent_thinking.json",
    QuestionType.CREATIVE_PROBLEM_SOLVING.value: "creative_problem_solving.json",
    QuestionType.IMAGINATION.value: "imagination.json",
}

TEMPLATES = {
    QuestionType.DIVERGENT_THINKING.value: {
        "title": "发散思维题 {idx}",
        "content": "请尽可能多地列举出{主题}的用途。至少写出10个不同的用途。",
        "dimensions": [CreativityDimension.FLUENCY.value, CreativityDimension.FLEXIBILITY.value],
    },
    QuestionType.CONVERGENT_THINKING.value: {
        "title": "聚合思维题 {idx}",
        "content": "请找出以下物品的共同点：{物品列表}。至少找出5个共同特征。",
        "dimensions": [CreativityDimension.FLEXIBILITY.value, CreativityDimension.ORIGINALITY.value],
    },
    QuestionType.CREATIVE_PROBLEM_SOLVING.value: {
        "title": "创造性问题解决 {idx}",
        "content": "请设计一个创新的解决方案来解决以下问题：{问题描述}。",
        "dimensions": [CreativityDimension.ORIGINALITY.value, CreativityDimension.ELABORATION.value],
    },
    QuestionType.IMAGINATION.value: {
        "title": "想象力测试 {idx}",
        "content": "请描述一个想象中的{场景}，要求具有创新性和独特性。",
        "dimensions": [CreativityDimension.ORIGINALITY.value, CreativityDimension.ELABORATION.value],
    },
}

THEMES = ["砖头", "回形针", "报纸", "雨伞", "橡皮筋", "塑料瓶", "绳子", "纸箱", "勺子", "旧衣服"]
ITEM_LISTS = [
    "苹果、橙子、香蕉", "汽车、飞机、轮船", "书、电脑、手机", "钢笔、铅笔、记号笔",
    "山、河、湖", "桌子、椅子、柜子", "猫、狗、鸟"
]
PROBLEMS = [
    "如何让城市更环保", "如何提高学习效率", "如何减少交通拥堵", "如何降低校园垃圾",
    "如何节约用水", "如何减少食物浪费", "如何提升社区安全"
]
SCENES = ["未来学校", "外星球", "海底城市", "天空之城", "微缩世界", "蒸汽朋克城市"]

_cache: Dict[str, List[Dict]] = {}


def _ensure_dir() -> None:
    if not os.path.isdir(QUESTIONS_DIR):
        os.makedirs(QUESTIONS_DIR, exist_ok=True)


def _build_item(qtype: str, idx: int) -> Dict:
    tpl = TEMPLATES[qtype]
    content = tpl["content"].format(
        主题=random.choice(THEMES),
        物品列表=random.choice(ITEM_LISTS),
        问题描述=random.choice(PROBLEMS),
        场景=random.choice(SCENES),
    )
    return {
        "id": f"{qtype[:3]}_{idx}",
        "type": qtype,
        "title": tpl["title"].format(idx=idx),
        "content": content,
        "time_limit": 300,
        "dimensions": tpl["dimensions"],
        "scoring_criteria": {
            "fluency_weight": 0.3,
            "flexibility_weight": 0.3,
            "originality_weight": 0.2,
            "elaboration_weight": 0.2,
        },
        "generated_at": datetime.now().isoformat(),
    }


def ensure_question_files(count_per_type: int = 100) -> None:
    """若题库文件不存在则自动生成每类 count_per_type 道题。"""
    _ensure_dir()
    for qtype, fname in FILE_MAP.items():
        fpath = os.path.join(QUESTIONS_DIR, fname)
        if not os.path.exists(fpath):
            data = [_build_item(qtype, i + 1) for i in range(count_per_type)]
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


def load_questions() -> Dict[str, List[Dict]]:
    """加载题库到内存（带缓存）。返回 dict: qtype -> list[question dict]"""
    if _cache:
        return _cache
    ensure_question_files()
    result: Dict[str, List[Dict]] = {}
    for qtype, fname in FILE_MAP.items():
        fpath = os.path.join(QUESTIONS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                result[qtype] = json.load(f)
        except Exception:
            result[qtype] = []
    _cache.update(result)
    return _cache


def sample_questions_per_type(num_total: int) -> List[Dict]:
    """按各类型均衡或随机抽样合计 num_total 道题。"""
    bank = load_questions()
    # 简单均匀分配
    types = list(bank.keys())
    per = max(1, num_total // max(1, len(types)))
    sampled: List[Dict] = []
    for t in types:
        pool = bank.get(t, [])
        if not pool:
            continue
        k = min(per, len(pool))
        sampled.extend(random.sample(pool, k))
    # 若不足，继续从所有池中补齐
    if len(sampled) < num_total:
        all_pool = [q for lst in bank.values() for q in lst]
        remaining = num_total - len(sampled)
        if all_pool:
            sampled.extend(random.sample(all_pool, min(remaining, len(all_pool))))
    # 打乱
    random.shuffle(sampled)
    return sampled[:num_total]
