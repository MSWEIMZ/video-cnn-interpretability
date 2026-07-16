"""配置加载与校验模块"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class FilterConfig:
    years_from: int = 2015
    years_to: int = 2026
    allowed_categories: list[str] = field(default_factory=lambda: ["cs.CV", "cs.LG", "cs.AI"])
    blocked_keywords: list[str] = field(default_factory=list)
    required_domain_keywords: list[str] = field(default_factory=lambda: [
        "video", "action recognition", "spatiotemporal", "spatio-temporal",
        "space-time", "3d cnn", "3d convolution", "optical flow",
    ])
    required_topic_keywords: list[str] = field(default_factory=list)


@dataclass
class ScoringConfig:
    min_relevance_score: float = 2.5
    core_threshold: float = 4.0
    strongly_related_threshold: float = 2.5
    keyword_weights: dict[str, float] = field(default_factory=lambda: {"core": 2.0, "expanded": 1.0, "exploratory": 0.5})
    category_bonus: dict[str, float] = field(default_factory=lambda: {"cs.CV": 1.0, "cs.LG": 0.5, "cs.AI": 0.3})
    topic_bonus_per_hit: float = 0.3
    blocked_penalty: float = 10.0
    video_in_title_bonus: float = 0.5
    survey_bonus: float = 0.8
    venue_bonus: dict[str, float] = field(default_factory=lambda: {
        "CVPR": 0.5, "ICCV": 0.5, "ECCV": 0.5,
        "NeurIPS": 0.4, "ICML": 0.4, "ICLR": 0.4,
        "AAAI": 0.3,
    })
    citation_bonus_threshold: int = 50
    citation_bonus: float = 0.5


@dataclass
class RuntimeConfig:
    max_results_per_query: int = 30
    output_dir: str = "papers"
    index_format: str = "jsonl"
    write_markdown_cards: bool = False
    write_readme: bool = True
    notify_feishu: bool = True
    legacy_years_filter: list[int] = field(default_factory=lambda: [2021, 2026])
    lookback_days: int = 14
    semantic_scholar_enabled: bool = True
    semantic_scholar_queries_per_run: int = 2
    crossref_enabled: bool = True
    crossref_max_new_per_run: int = 20


@dataclass
class AppConfig:
    core_queries: list[str] = field(default_factory=list)
    expanded_queries: list[str] = field(default_factory=list)
    exploratory_queries: list[str] = field(default_factory=list)
    filters: FilterConfig = field(default_factory=FilterConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)


def load_app_config(path: str | Path) -> AppConfig:
    """加载并校验配置文件，返回 AppConfig 实例"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"配置文件不存在: {p}")
    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    queries = raw.get("queries", {})
    if not queries.get("core"):
        raise ValueError("配置缺少 queries.core")

    f_raw = raw.get("filters", {})
    years_to_raw = f_raw.get("years_to", "current")
    years_to = datetime.now().year if years_to_raw == "current" else years_to_raw
    filters = FilterConfig(
        years_from=f_raw.get("years_from", 2015),
        years_to=years_to,
        allowed_categories=f_raw.get("allowed_categories", ["cs.CV", "cs.LG", "cs.AI"]),
        blocked_keywords=f_raw.get("blocked_keywords", []),
        required_domain_keywords=f_raw.get("required_domain_keywords", [
            "video", "action recognition", "spatiotemporal", "spatio-temporal",
            "space-time", "3d cnn", "3d convolution", "optical flow",
        ]),
        required_topic_keywords=f_raw.get("required_topic_keywords", []),
    )

    s_raw = raw.get("scoring", {})
    scoring = ScoringConfig(
        min_relevance_score=s_raw.get("min_relevance_score", 2.5),
        core_threshold=s_raw.get("core_threshold", 4.0),
        strongly_related_threshold=s_raw.get("strongly_related_threshold", 2.5),
        keyword_weights=s_raw.get("keyword_weights", {"core": 2.0, "expanded": 1.0, "exploratory": 0.5}),
        category_bonus=s_raw.get("category_bonus", {"cs.CV": 1.0, "cs.LG": 0.5, "cs.AI": 0.3}),
        topic_bonus_per_hit=s_raw.get("topic_bonus_per_hit", 0.3),
        blocked_penalty=s_raw.get("blocked_penalty", 10.0),
        video_in_title_bonus=s_raw.get("video_in_title_bonus", 0.5),
        survey_bonus=s_raw.get("survey_bonus", 0.8),
        venue_bonus=s_raw.get("venue_bonus", {
            "CVPR": 0.5, "ICCV": 0.5, "ECCV": 0.5,
            "NeurIPS": 0.4, "ICML": 0.4, "ICLR": 0.4, "AAAI": 0.3,
        }),
        citation_bonus_threshold=s_raw.get("citation_bonus_threshold", 50),
        citation_bonus=s_raw.get("citation_bonus", 0.5),
    )

    r_raw = raw.get("runtime", {})
    runtime = RuntimeConfig(
        max_results_per_query=r_raw.get("max_results_per_query", 30),
        output_dir=r_raw.get("output_dir", "papers"),
        index_format=r_raw.get("index_format", "jsonl"),
        write_markdown_cards=r_raw.get("write_markdown_cards", False),
        write_readme=r_raw.get("write_readme", True),
        notify_feishu=r_raw.get("notify_feishu", True),
        legacy_years_filter=r_raw.get("legacy_years_filter", [2021, 2026]),
        lookback_days=r_raw.get("lookback_days", 14),
        semantic_scholar_enabled=r_raw.get("semantic_scholar_enabled", True),
        semantic_scholar_queries_per_run=r_raw.get("semantic_scholar_queries_per_run", 2),
        crossref_enabled=r_raw.get("crossref_enabled", True),
        crossref_max_new_per_run=r_raw.get("crossref_max_new_per_run", 20),
    )

    if not isinstance(filters.years_from, int) or not isinstance(filters.years_to, int):
        raise ValueError("filters.years_from/years_to 必须为整数或 years_to='current'")
    if filters.years_from > filters.years_to:
        raise ValueError("filters.years_from 不能大于 years_to")
    if not filters.allowed_categories or not all(isinstance(v, str) for v in filters.allowed_categories):
        raise ValueError("filters.allowed_categories 必须为非空字符串列表")
    if not filters.required_domain_keywords or not all(
        isinstance(value, str) and value.strip() for value in filters.required_domain_keywords
    ):
        raise ValueError("filters.required_domain_keywords 必须为非空字符串列表")
    if not (
        scoring.min_relevance_score
        <= scoring.strongly_related_threshold
        <= scoring.core_threshold
    ):
        raise ValueError("评分阈值必须满足 min <= strongly_related <= core")
    if runtime.max_results_per_query <= 0 or runtime.lookback_days <= 0:
        raise ValueError("runtime.max_results_per_query/lookback_days 必须大于 0")
    if runtime.semantic_scholar_queries_per_run < 0 or runtime.crossref_max_new_per_run < 0:
        raise ValueError("来源请求上限不能为负数")

    return AppConfig(
        core_queries=queries.get("core", []),
        expanded_queries=queries.get("expanded", []),
        exploratory_queries=queries.get("exploratory", []),
        filters=filters,
        scoring=scoring,
        runtime=runtime,
    )

