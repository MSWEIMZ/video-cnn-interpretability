"""论文相关性评分模块"""
from __future__ import annotations
from .config import AppConfig, ScoringConfig


# ---------- 顶级会议加分表 ----------
_TOP_TIER_VENUES: dict[str, float] = {
    "cvpr": 0.5, "iccv": 0.5, "eccv": 0.5,
    "neurips": 0.4, "icml": 0.4, "iclr": 0.4,
    "aaai": 0.3, "ijcai": 0.3,
}

# ---------- 综述/基准关键词 ----------
_SURVEY_KEYWORDS: list[str] = [
    "survey", "review", "benchmark", "taxonomy", "comprehensive review",
]


def _text_contains(text: str, keywords: list[str]) -> list[str]:
    """返回 text 中命中的关键词列表"""
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def is_video_domain_relevant(paper: dict, domain_keywords: list[str]) -> bool:
    """要求标题或摘要包含明确的视频/时空视觉领域证据。"""
    title = paper.get("title", "")
    abstract = paper.get("summary", paper.get("abstract", ""))
    return bool(_text_contains(f"{title} {abstract}", domain_keywords))


# ---------- 新增辅助函数 ----------

def _detect_venue_bonus(text: str, venue_bonuses: dict[str, float] | None = None) -> float:
    """从文本中检测顶级会议名称并返回加分值（取最高值）"""
    if venue_bonuses is None:
        venue_bonuses = _TOP_TIER_VENUES
    text_lower = text.lower()
    best_bonus = 0.0
    for venue, bonus in venue_bonuses.items():
        if venue.lower() in text_lower:
            best_bonus = max(best_bonus, bonus)
    return best_bonus


def _detect_survey_bonus(text: str, bonus: float = 0.8) -> float:
    """检测综述/基准关键词，命中则返回配置的加分。"""
    text_lower = text.lower()
    if any(kw in text_lower for kw in _SURVEY_KEYWORDS):
        return bonus
    return 0.0


def _apply_citation_bonus(citation_count: int, threshold: int = 50, bonus: float = 0.5) -> float:
    """引用量达到阈值则加分"""
    if citation_count >= threshold:
        return bonus
    return 0.0


# ---------- 主评分函数 ----------

def compute_relevance_score(paper: dict, query_type: str, config: AppConfig) -> float:
    """计算论文相关性分数
    
    评分规则:
    - 查询类型基础分: core=2, expanded=1, exploratory=0.5
    - 类别加分: cs.CV=1.0, cs.LG=0.5
    - 主题关键词命中: 每个+0.3
    - 标题包含 video/action/temporal: +0.5
    - 引用量>=50: +0.5
    - 顶级 venue 加分: CVPR/ICCV/ECCV +0.5, NeurIPS/ICML/ICLR +0.4, AAAI/IJCAI +0.3
    - 综述/基准识别: +0.8
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

    # --- 新增评分维度 ---

    # 引用量信号
    citation_count = paper.get("citation_count", 0)
    score += _apply_citation_bonus(
        citation_count,
        threshold=sc.citation_bonus_threshold,
        bonus=sc.citation_bonus,
    )

    # Venue 加分：从 venue 和 journal_ref 字段检测
    venue_text = f"{paper.get('venue', '')} {paper.get('journal_ref', '')}"
    score += _detect_venue_bonus(venue_text, sc.venue_bonus)

    # 综述/基准识别
    score += _detect_survey_bonus(combined, sc.survey_bonus)

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
