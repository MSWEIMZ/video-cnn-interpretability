"""论文数据规范化模块"""
from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class PaperRecord:
    """标准化论文记录"""
    canonical_id: str = ""
    version: int = 1
    arxiv_id: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: int = 0
    published: str = ""
    updated: str = ""
    primary_category: str = ""
    categories: list[str] = field(default_factory=list)
    abstract: str = ""
    url: str = ""
    pdf_url: str = ""
    journal_ref: str = ""
    search_category: str = ""   # core / expanded / exploratory
    search_query: str = ""
    query_type: str = ""        # core / expanded / exploratory
    relevance_score: float = 0.0
    quality_label: str = ""     # core / strongly_related / weakly_related / noise
    markdown_path: str = ""

    def to_dict(self) -> dict:
        return {
            "canonical_id": self.canonical_id,
            "version": self.version,
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "published": self.published,
            "updated": self.updated,
            "primary_category": self.primary_category,
            "categories": self.categories,
            "abstract": self.abstract,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "journal_ref": self.journal_ref,
            "search_category": self.search_category,
            "search_query": self.search_query,
            "query_type": self.query_type,
            "relevance_score": self.relevance_score,
            "quality_label": self.quality_label,
            "markdown_path": self.markdown_path,
        }


def normalize_arxiv_id(raw_id: str) -> tuple[str, int]:
    """将 arxiv ID 规范化为 (canonical_id, version)
    
    例: '2603.04976v2' -> ('2603.04976', 2)
         '2603.04976'   -> ('2603.04976', 1)
    """
    if not raw_id:
        return ("unknown", 1)
    # 去掉可能的 URL 前缀
    raw_id = raw_id.split("/")[-1]
    match = re.match(r"^(\d{4}\.\d{4,5})(?:v(\d+))?$", raw_id)
    if match:
        canonical = match.group(1)
        version = int(match.group(2)) if match.group(2) else 1
        return (canonical, version)
    return (raw_id, 1)


def extract_year_from_arxiv_id(arxiv_id: str) -> int:
    """从 arXiv ID 提取年份，如 2603.04976 -> 2026"""
    match = re.match(r"(\d{2})(\d{2})", arxiv_id)
    if match:
        year_prefix = int(match.group(1))
        year_suffix = int(match.group(2))
        year = 2000 + year_prefix if year_prefix < 90 else 1900 + year_prefix
        # 月份大于12时属于下一年的预印本
        if year_suffix > 12:
            year += 1
        return year
    return 2020


def extract_year(published: str, arxiv_id: str) -> int:
    """从 published 日期或 arxiv_id 提取年份"""
    if published and len(published) >= 4:
        try:
            return int(published[:4])
        except ValueError:
            pass
    return extract_year_from_arxiv_id(arxiv_id)


def build_paper_record(raw: dict, query_type: str, search_query: str) -> PaperRecord:
    """从 arXiv API 原始数据构建标准化论文记录"""
    raw_id = raw.get("arxiv_id", raw.get("arxiv_url", "").split("/")[-1])
    canonical_id, version = normalize_arxiv_id(raw_id)
    published = raw.get("published", "")
    year = extract_year(published, canonical_id)
    categories = raw.get("categories", [])
    primary = categories[0] if categories else ""

    return PaperRecord(
        canonical_id=canonical_id,
        version=version,
        arxiv_id=raw_id,
        title=raw.get("title", "").strip(),
        authors=raw.get("authors", []),
        year=year,
        published=published,
        updated=raw.get("updated", ""),
        primary_category=primary,
        categories=categories,
        abstract=raw.get("summary", "").strip(),
        url=raw.get("arxiv_url", ""),
        pdf_url=raw.get("pdf_url", ""),
        journal_ref=raw.get("journal_ref", ""),
        query_type=query_type,
        search_query=search_query,
    )
