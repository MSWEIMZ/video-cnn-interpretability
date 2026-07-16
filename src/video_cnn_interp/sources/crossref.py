"""CrossRef 元数据增强：仅在标题高置信匹配时写入引用和 Venue。"""
from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from urllib.parse import urlencode
from urllib.request import Request, urlopen


_BASE_URL = "https://api.crossref.org/works"


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def _published_year(item: dict) -> int | None:
    for field in ["published-print", "published-online", "published", "created"]:
        parts = item.get(field, {}).get("date-parts", [])
        if parts and parts[0]:
            try:
                return int(parts[0][0])
            except (TypeError, ValueError, IndexError):
                continue
    return None


def select_best_match(record: dict, items: list[dict], min_similarity: float = 0.90) -> dict | None:
    title = record.get("title", "")
    year = int(record.get("year", 0) or 0)
    best: tuple[float, dict] | None = None
    for item in items:
        candidate_titles = item.get("title") or []
        if not candidate_titles:
            continue
        similarity = title_similarity(title, candidate_titles[0])
        item_year = _published_year(item)
        if year and item_year and abs(year - item_year) > 2:
            continue
        if similarity < min_similarity:
            continue
        if best is None or similarity > best[0]:
            best = (similarity, item)
    return best[1] if best else None


def enrich_record(record: dict, timeout: int = 15) -> dict:
    """返回增强后的副本；匹配不足时保持原记录不变。"""
    if not record.get("title"):
        return dict(record)
    params = {
        "query.title": record["title"],
        "rows": 3,
        "select": "DOI,title,is-referenced-by-count,container-title,published,published-print,published-online,created",
    }
    mailto = os.environ.get("CROSSREF_MAILTO", "")
    if mailto:
        params["mailto"] = mailto
    request = Request(
        f"{_BASE_URL}?{urlencode(params)}",
        headers={"User-Agent": "video-cnn-xai-research-hub/2.1"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"  [WARN] CrossRef 增强失败: {exc}")
        return dict(record)

    match = select_best_match(record, payload.get("message", {}).get("items", []))
    if not match:
        return dict(record)

    result = dict(record)
    result["citation_count"] = max(
        int(result.get("citation_count", 0) or 0),
        int(match.get("is-referenced-by-count", 0) or 0),
    )
    venues = match.get("container-title") or []
    if not result.get("venue") and venues:
        result["venue"] = venues[0]
    if match.get("DOI"):
        result["doi"] = match["DOI"]
    sources = list(result.get("sources", []) or [])
    if result.get("source") and result["source"] not in sources:
        sources.append(result["source"])
    if "crossref" not in sources:
        sources.append("crossref")
    result["sources"] = sources
    return result
