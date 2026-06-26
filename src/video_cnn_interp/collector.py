"""arXiv 论文收集模块（支持多源：arXiv + Semantic Scholar）"""
from __future__ import annotations
import re
import ssl
import time
from difflib import SequenceMatcher
from urllib.request import urlopen, Request
from urllib.parse import urlencode

from .config import AppConfig
from .sources.semantic_scholar import search_semantic_scholar

try:
    import arxiv
    USE_ARXIV_LIB = True
except ImportError:
    USE_ARXIV_LIB = False


def _search_arxiv_lib(query: str, max_results: int) -> list[dict]:
    """使用 arxiv 库搜索"""
    papers = []
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
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


def _search_arxiv_manual(query: str, max_results: int) -> list[dict]:
    """手动调用 arXiv API 搜索"""
    base_url = "http://export.arxiv.org/api/query?"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = base_url + urlencode(params)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urlopen(url, timeout=30, context=ctx) as resp:
            data = resp.read().decode("utf-8")
            return _parse_arxiv_xml(data)
    except Exception as e:
        print(f"  [WARN] arXiv API 请求失败: {e}")
        return []


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


def _search_one_query(query: str, max_results: int) -> list[dict]:
    """执行单条 arXiv 查询"""
    if USE_ARXIV_LIB:
        return _search_arxiv_lib(query, max_results)
    return _search_arxiv_manual(query, max_results)


def _pre_filter(paper: dict, blocked_keywords: list[str]) -> bool:
    """返回 True 表示应被阻断（命中黑名单）"""
    text = (paper.get("title", "") + " " + paper.get("summary", "")).lower()
    return any(kw.lower() in text for kw in blocked_keywords)


def _is_duplicate(paper_a: dict, paper_b: dict) -> bool:
    """判断两篇论文是否为重复论文"""
    id_a = paper_a.get("arxiv_id", "")
    id_b = paper_b.get("arxiv_id", "")
    if id_a and id_b and id_a == id_b:
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


def collect_candidates(config: AppConfig) -> list[tuple[str, str, dict]]:
    """收集候选论文（调用多源版本）"""
    return collect_candidates_multi_source(config)


def collect_candidates_multi_source(config: AppConfig) -> list[tuple[str, str, dict]]:
    """多源收集候选论文，返回 [(query_type, search_query, paper_dict), ...]"""
    max_results = config.runtime.max_results_per_query
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
            raw_papers = _search_one_query(query, max_results)
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
    ss_groups = [
        ("core", config.core_queries),
        ("expanded", config.expanded_queries),
    ]
    for query_type, queries in ss_groups:
        print(f"\n[{query_type} 查询 - Semantic Scholar]")
        for query in queries:
            print(f"  搜索: {query}")
            raw_papers = search_semantic_scholar(
                query=query,
                year_range=year_range,
                max_results=max_results,
            )
            print(f"  原始结果: {len(raw_papers)} 篇")
            new_papers = _deduplicate(raw_papers, seen_ids)
            kept = 0
            for paper in new_papers:
                if _pre_filter(paper, blocked):
                    continue
                candidates.append((query_type, query, paper))
                kept += 1
            print(f"  去重后新论文: {len(new_papers)} 篇，通过预过滤: {kept} 篇")

    print(f"\n候选池总计: {len(candidates)} 篇论文（多源合并后）")
    return candidates
