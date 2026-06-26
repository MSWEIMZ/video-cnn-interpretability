"""论文相关性评分模块"""
from __future__ import annotations
from .config import AppConfig, ScoringConfig


def _text_contains(text: str, keywords: list[str]) -> list[str]:
    """返回 text 中命中的关键词列表"""
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def compute_relevance_score(paper: dict, query_type: str, config: AppConfig) -> float:
    """计算论文相关性分数
    
    评分规则:
    - 查询类型基础分: core=2, expanded=1, exploratory=0.5
    - 类别加分: cs.CV=1.0, cs.LG=0.5
    - 主题关键词命中: 每个+0.3
    - 标题包含 video/action/temporal: +0.5
    - 命中阻断关键词: -10.0
    """
    sc = config.scoring
    score = sc.keyword_weights.get(query_type, 0.5)

    # 类别加分
    categories = paper.get("categories", [])
    for cat in categories:
        score += sc.category_bonus.get(cat, 0.0)

    # 主题关键词命中
    title = paper.get("title", "")
    abstract = paper.get("summary", paper.get("abstract", ""))
    combined = f"{title} {abstract}"
    topic_hits = _text_contains(combined, config.filters.required_topic_keywords)
    score += len(topic_hits) * sc.topic_bonus_per_hit

    # 标题含视频相关词加分
    video_keywords = ["video", "action", "temporal", "spatiotemporal", "R(2+1)D", "3D CNN"]
    if _text_contains(title, video_keywords):
        score += sc.video_in_title_bonus

    # 阻断关键词惩罚
    blocked_hits = _text_contains(combined, config.filters.blocked_keywords)
    if blocked_hits:
        score -= sc.blocked_penalty

    return round(score, 2)


def assign_quality_label(score: float, config: AppConfig) -> str:
    """根据分数分配质量标签"""
    sc = config.scoring
    if score >= sc.core_threshold:
        return "core"
    if score >= sc.strongly_related_threshold:
        return "strongly_related"
    if score >= sc.min_relevance_score:
        return "weakly_related"
    return "noise"


def should_block(paper: dict, blocked_keywords: list[str]) -> bool:
    """快速阻断检查：是否命中黑名单关键词"""
    title = paper.get("title", "").lower()
    abstract = paper.get("summary", paper.get("abstract", "")).lower()
    combined = f"{title} {abstract}"
    return any(kw.lower() in combined for kw in blocked_keywords)
