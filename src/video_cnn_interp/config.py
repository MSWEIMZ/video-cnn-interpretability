"""配置加载与校验模块"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FilterConfig:
    years_from: int = 2015
    years_to: int = 2026
    allowed_categories: list[str] = field(default_factory=lambda: ["cs.CV", "cs.LG"])
    blocked_keywords: list[str] = field(default_factory=list)
    required_topic_keywords: list[str] = field(default_factory=list)


@dataclass
class ScoringConfig:
    min_relevance_score: float = 2.0
    core_threshold: float = 4.0
    strongly_related_threshold: float = 2.5
    keyword_weights: dict[str, float] = field(default_factory=lambda: {"core": 2.0, "expanded": 1.0, "exploratory": 0.5})
    category_bonus: dict[str, float] = field(default_factory=lambda: {"cs.CV": 1.0, "cs.LG": 0.5})
    topic_bonus_per_hit: float = 0.3
    blocked_penalty: float = 10.0
    video_in_title_bonus: float = 0.5


@dataclass
class RuntimeConfig:
    max_results_per_query: int = 30
    output_dir: str = "papers"
    index_format: str = "jsonl"
    write_markdown_cards: bool = True
    write_readme: bool = True
    notify_feishu: bool = True
    legacy_years_filter: list[int] = field(default_factory=lambda: [2021, 2026])


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
    filters = FilterConfig(
        years_from=f_raw.get("years_from", 2015),
        years_to=f_raw.get("years_to", 2026),
        allowed_categories=f_raw.get("allowed_categories", ["cs.CV", "cs.LG"]),
        blocked_keywords=f_raw.get("blocked_keywords", []),
        required_topic_keywords=f_raw.get("required_topic_keywords", []),
    )

    s_raw = raw.get("scoring", {})
    scoring = ScoringConfig(
        min_relevance_score=s_raw.get("min_relevance_score", 2.0),
        core_threshold=s_raw.get("core_threshold", 4.0),
        strongly_related_threshold=s_raw.get("strongly_related_threshold", 2.5),
        keyword_weights=s_raw.get("keyword_weights", {"core": 2.0, "expanded": 1.0, "exploratory": 0.5}),
        category_bonus=s_raw.get("category_bonus", {"cs.CV": 1.0, "cs.LG": 0.5}),
        topic_bonus_per_hit=s_raw.get("topic_bonus_per_hit", 0.3),
        blocked_penalty=s_raw.get("blocked_penalty", 10.0),
        video_in_title_bonus=s_raw.get("video_in_title_bonus", 0.5),
    )

    r_raw = raw.get("runtime", {})
    runtime = RuntimeConfig(
        max_results_per_query=r_raw.get("max_results_per_query", 30),
        output_dir=r_raw.get("output_dir", "papers"),
        index_format=r_raw.get("index_format", "jsonl"),
        write_markdown_cards=r_raw.get("write_markdown_cards", True),
        write_readme=r_raw.get("write_readme", True),
        notify_feishu=r_raw.get("notify_feishu", True),
        legacy_years_filter=r_raw.get("legacy_years_filter", [2021, 2026]),
    )

    return AppConfig(
        core_queries=queries.get("core", []),
        expanded_queries=queries.get("expanded", []),
        exploratory_queries=queries.get("exploratory", []),
        filters=filters,
        scoring=scoring,
        runtime=runtime,
    )
