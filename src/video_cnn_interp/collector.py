"""arXiv 论文收集模块（支持多源：arXiv + Semantic Scholar）"""
from __future__ import annotations
import re
import time
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from urllib.request import urlopen
from urllib.parse import urlencode

from .config import AppConfig
from .normalizer import normalize_arxiv_id
from .sources.semantic_scholar import search_semantic_scholar

try:
    import arxiv
    USE_ARXIV_LIB = True
except ImportError:
    USE_ARXIV_LIB = False


def _with_date_window(query: str, lookback_days: int | None) -> str:
    if not lookback_days:
        return query
    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days)
    return (
        f"({query}) AND submittedDate:"
        f"[{start.strftime('%Y%m%d0000')} TO {end.strftime('%Y%m%d2359')}]"
    )


def _search_arxiv_lib(query: str, max_results: int, lookback_days: int | None = None) -> list[dict]:
    """使用 arxiv 库搜索"""
    papers = []
    client = arxiv.Client()
    search = arxiv.Search(
        query=_with_date_window(query, lookback_days),
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    for result in client.results(search):
        papers.append({
            "title": result.title.strip(),
            "authors": [a.name for a in result.authors],
            "summary": result.summary.strip(),
            "arxiv_url": result.entry_id,
            "arxiv_id": result.get_short_id(),
            "published": str(result.published.date()),
            "updated": str(result.updated.date()) if result.updated else "",
            "pdf_url": result.pdf_url,
            "categories": [c for c in result.categories if c.startswith("cs.")],
            "primary_category": result.primary_category,
            "journal_ref": getattr(result, "journal_ref", None) or "",
            "citation_count": 0,
            "venue": "",
            "source": "arxiv",
        })
    return papers


def _search_arxiv_manual(query: str, max_results: int, lookback_days: int | None = None) -> list[dict]:
    """手动调用 arXiv API 搜索"""
    base_url = "https://export.arxiv.org/api/query?"
    params = {
        "search_query": _with_date_window(f"all:{query}", lookback_days),
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = base_url + urlencode(params)
    with urlopen(url, timeout=30) as resp:
        data = resp.read().decode("utf-8")
        return _parse_arxiv_xml(data)


def _parse_arxiv_xml(xml_data: str) -> list[dict]:
    """解析 arXiv XML 响应"""
    papers = []
    entries = re.findall(r"<entry>(.*?)</entry>", xml_data, re.DOTALL)
    for entry in entries:
        paper: dict = {}
        title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        if title_m:
            paper["title"] = " ".join(title_m.group(1).split())
        authors = re.findall(r"<name>(.*?)</name>", entry)
        paper["authors"] = authors or ["Unknown"]
        summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        if summary_m:
            paper["summary"] = " ".join(summary_m.group(1).split())
        id_m = re.search(r"<id>(.*?)</id>", entry)
        if id_m:
            paper["arxiv_url"] = id_m.group(1)
            paper["arxiv_id"] = id_m.group(1).split("/")[-1]
        pub_m = re.search(r"<published>(.*?)</published>", entry)
        if pub_m:
            paper["published"] = pub_m.group(1)[:10]
        upd_m = re.search(r"<updated>(.*?)</updated>", entry)
        if upd_m:
            paper["updated"] = upd_m.group(1)[:10]
        pdf_m = re.search(r'<link[^>]*title="pdf"[^>]*href="(.*?)"', entry)
        if pdf_m:
            paper["pdf_url"] = pdf_m.group(1)
        cats = re.findall(r'<category term="([^"]*)"', entry)
        paper["categories"] = [c for c in cats if c.startswith("cs.")]
        paper["primary_category"] = paper["categories"][0] if paper["categories"] else ""
        jr_m = re.search(r"<journal-ref>(.*?)</journal-ref>", entry, re.DOTALL)
        paper["journal_ref"] = jr_m.group(1).strip() if jr_m else ""
        paper["citation_count"] = 0
        paper["venue"] = ""
        paper["source"] = "arxiv"
        if paper.get("title"):
            papers.append(paper)
    return papers


def _search_one_query(query: str, max_results: int, lookback_days: int | None = None) -> list[dict]:
    """执行单条 arXiv 查询"""
    if USE_ARXIV_LIB:
        return _search_arxiv_lib(query, max_results, lookback_days)
    return _search_arxiv_manual(query, max_results, lookback_days)


def _pre_filter(paper: dict, blocked_keywords: list[str]) -> bool:
    """返回 True 表示应被阻断（命中黑名单）"""
    text = (paper.get("title", "") + " " + paper.get("summary", "")).lower()
    return any(kw.lower() in text for kw in blocked_keywords)


def _is_duplicate(paper_a: dict, paper_b: dict) -> bool:
    """判断两篇论文是否为重复论文"""
    id_a = paper_a.get("arxiv_id", "")
    id_b = paper_b.get("arxiv_id", "")
    if id_a and id_b:
        canonical_a, _ = normalize_arxiv_id(id_a)
        canonical_b, _ = normalize_arxiv_id(id_b)
        if canonical_a == canonical_b:
            return True
    title_a = (paper_a.get("title") or "").lower().strip()
    title_b = (paper_b.get("title") or "").lower().strip()
    if title_a and title_b:
        ratio = SequenceMatcher(None, title_a, title_b).ratio()
        if ratio > 0.85:
            return True
    return False


def _deduplicate(papers: list[dict], seen_ids: set[str]) -> list[dict]:
    """对论文列表去重，返回不重复的新论文"""
    unique = []
    for paper in papers:
        pid = paper.get("arxiv_id", "") or paper.get("title", "")
        if pid in seen_ids:
            continue
        is_dup = False
        for existing in unique:
            if _is_duplicate(paper, existing):
                is_dup = True
                break
        if not is_dup:
            seen_ids.add(pid)
            unique.append(paper)
    return unique


def _title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def _merge_raw_papers(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    merged["citation_count"] = max(
        int(existing.get("citation_count", 0) or 0),
        int(incoming.get("citation_count", 0) or 0),
    )
    for field in ["venue", "journal_ref", "pdf_url", "summary", "categories", "primary_category"]:
        if not merged.get(field) and incoming.get(field):
            merged[field] = incoming[field]
    sources = []
    for source in [
        *(existing.get("sources", []) or []),
        existing.get("source"),
        *(incoming.get("sources", []) or []),
        incoming.get("source"),
    ]:
        if source and source not in sources:
            sources.append(source)
    if sources:
        merged["sources"] = sources
    return merged


def _deduplicate_candidates(
    candidates: list[tuple[str, str, dict]],
) -> list[tuple[str, str, dict]]:
    """按 arXiv ID 和规范化标题做跨来源去重，同时合并引用与 venue。"""
    result: list[tuple[str, str, dict]] = []
    id_to_position: dict[str, int] = {}
    title_to_position: dict[str, int] = {}
    query_priority = {"core": 3, "expanded": 2, "exploratory": 1}

    for query_type, query, paper in candidates:
        raw_id = paper.get("arxiv_id", "")
        canonical_id, _ = normalize_arxiv_id(raw_id) if raw_id else ("", 1)
        title_key = _title_key(paper.get("title", ""))
        position = id_to_position.get(canonical_id) if canonical_id else None
        if position is None and title_key:
            position = title_to_position.get(title_key)

        if position is None:
            position = len(result)
            result.append((query_type, query, dict(paper)))
        else:
            old_type, old_query, old_paper = result[position]
            merged_paper = _merge_raw_papers(old_paper, paper)
            if query_priority.get(query_type, 0) > query_priority.get(old_type, 0):
                result[position] = (query_type, query, merged_paper)
            else:
                result[position] = (old_type, old_query, merged_paper)

        if canonical_id:
            id_to_position[canonical_id] = position
        if title_key:
            title_to_position[title_key] = position
    return result


def collect_candidates(config: AppConfig) -> list[tuple[str, str, dict]]:
    """收集候选论文（调用多源版本）"""
    return collect_candidates_multi_source(config)


def collect_candidates_multi_source(config: AppConfig) -> list[tuple[str, str, dict]]:
    """多源收集候选论文，返回 [(query_type, search_query, paper_dict), ...]"""
    max_results = config.runtime.max_results_per_query
    lookback_days = config.runtime.lookback_days
    blocked = config.filters.blocked_keywords
    year_range = f"{config.filters.years_from}-{config.filters.years_to}"
    candidates: list[tuple[str, str, dict]] = []
    seen_ids: set[str] = set()

    query_groups = [
        ("core", config.core_queries),
        ("expanded", config.expanded_queries),
        ("exploratory", config.exploratory_queries),
    ]

    print("\n" + "=" * 50)
    print("阶段 1：arXiv 搜索")
    print("=" * 50)
    for query_type, queries in query_groups:
        print(f"\n[{query_type} 查询]")
        for query in queries:
            print(f"  搜索: {query}")
            raw_papers = _search_one_query(query, max_results, lookback_days)
            print(f"  原始结果: {len(raw_papers)} 篇")
            kept = 0
            for paper in raw_papers:
                pid = paper.get("arxiv_id", "")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                if _pre_filter(paper, blocked):
                    continue
                candidates.append((query_type, query, paper))
                kept += 1
            print(f"  通过预过滤: {kept} 篇")
            time.sleep(3)

    print("\n" + "=" * 50)
    print("阶段 2：Semantic Scholar 搜索")
    print("=" * 50)
    ss_queries = [
        (query_type, query)
        for query_type, queries in [
            ("core", config.core_queries),
            ("expanded", config.expanded_queries),
        ]
        for query in queries
    ]
    ss_limit = config.runtime.semantic_scholar_queries_per_run
    if ss_queries and ss_limit:
        offset = date.today().toordinal() % len(ss_queries)
        ss_queries = (ss_queries[offset:] + ss_queries[:offset])[:ss_limit]
    else:
        ss_queries = []
    if not config.runtime.semantic_scholar_enabled:
        ss_queries = []

    for query_type, query in ss_queries:
        print(f"\n[{query_type} 查询 - Semantic Scholar]")
        print(f"  搜索: {query}")
        raw_papers = search_semantic_scholar(
            query=query,
            year_range=year_range,
            max_results=max_results,
        )
        if raw_papers is None:
            print("  [WARN] Semantic Scholar 当前不可用，本轮停止继续请求")
            break
        print(f"  原始结果: {len(raw_papers)} 篇")
        new_papers = _deduplicate(raw_papers, seen_ids)
        kept = 0
        for paper in new_papers:
            if _pre_filter(paper, blocked):
                continue
            candidates.append((query_type, query, paper))
            kept += 1
        print(f"  去重后新论文: {len(new_papers)} 篇，通过预过滤: {kept} 篇")

    deduplicated = _deduplicate_candidates(candidates)
    print(f"\n候选池总计: {len(deduplicated)} 篇论文（多源合并后）")
    return deduplicated
