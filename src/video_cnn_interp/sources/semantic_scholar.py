"""Semantic Scholar 论文搜索源"""
from __future__ import annotations

import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError
import json

# Semantic Scholar 免费 API
_BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = "title,authors,abstract,year,citationCount,url,externalIds,venue,publicationTypes"
_RATE_LIMIT_DELAY = 1.0  # 请求间隔（秒）
_RETRY_DELAY = 5.0  # 429 退避（秒）
_MAX_RETRIES = 3


def _normalize_paper(raw: dict) -> dict:
    """将 Semantic Scholar 返回结果统一为标准 dict 结构"""
    # 尝试从 externalIds 提取 arxiv_id
    ext_ids = raw.get("externalIds") or {}
    arxiv_id = ext_ids.get("ArXiv", "")
    canonical_id = arxiv_id if arxiv_id else raw.get("paperId", "")

    # 构造 arxiv_url / pdf_url
    if arxiv_id:
        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    else:
        arxiv_url = raw.get("url", "")
        pdf_url = ""

    authors_list = raw.get("authors") or []
    author_names = [a.get("name", "Unknown") for a in authors_list]

    # categories: Semantic Scholar 不直接返回，留空
    categories: list[str] = []

    return {
        "title": (raw.get("title") or "").strip(),
        "authors": author_names,
        "summary": (raw.get("abstract") or "").strip(),
        "arxiv_url": arxiv_url,
        "arxiv_id": canonical_id,
        "published": str(raw.get("year", "")) + "-01-01" if raw.get("year") else "",
        "updated": "",
        "pdf_url": pdf_url,
        "categories": categories,
        "primary_category": "",
        "journal_ref": "",
        "citation_count": raw.get("citationCount", 0) or 0,
        "venue": raw.get("venue", "") or "",
        "source": "semantic_scholar",
    }


def _api_request(url: str) -> dict | None:
    """发送 GET 请求，带 429 重试逻辑"""
    for attempt in range(_MAX_RETRIES):
        try:
            req = Request(url, headers={"User-Agent": "video-cnn-interp/2.0"})
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 429:
                wait = _RETRY_DELAY * (attempt + 1)
                print(f"  [WARN] Semantic Scholar 429 限流，等待 {wait}s 后重试...")
                time.sleep(wait)
            else:
                print(f"  [WARN] Semantic Scholar HTTP 错误 {e.code}: {e}")
                return None
        except Exception as e:
            print(f"  [WARN] Semantic Scholar 请求异常: {e}")
            return None
    print("  [WARN] Semantic Scholar 重试次数耗尽")
    return None


def search_semantic_scholar(
    query: str,
    year_range: str = "2015-2026",
    max_results: int = 30,
    fields_of_study: str = "Computer Science",
) -> list[dict]:
    """搜索 Semantic Scholar 并返回标准化论文列表
    
    Args:
        query: 搜索关键词
        year_range: 年份范围，如 "2015-2026"
        max_results: 最大返回数量
        fields_of_study: 学科领域过滤
        
    Returns:
        标准化论文 dict 列表
    """
    params = {
        "query": query,
        "year": year_range,
        "fieldsOfStudy": fields_of_study,
        "fields": _FIELDS,
        "limit": min(max_results, 100),  # API 单次上限 100
    }
    url = f"{_BASE_URL}?{urlencode(params)}"
    
    data = _api_request(url)
    if not data or "data" not in data:
        return []

    papers = []
    for item in data["data"]:
        paper = _normalize_paper(item)
        if paper["title"]:
            papers.append(paper)

    # 限流
    time.sleep(_RATE_LIMIT_DELAY)
    return papers

