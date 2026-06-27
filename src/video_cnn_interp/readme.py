"""README 与 ALL_PAPERS 生成模块（支持中英文）"""
from __future__ import annotations
from datetime import datetime
from collections import defaultdict

# ── 语言包 ──────────────────────────────────────────────────────────────────
_I18N = {
    "zh": {
        "title": "# 📚 视频 CNN 可解释性论文库",
        "subtitle": "> 自动化论文搜索与整理系统 | 专注于 3DCNN、R(2+1)D 模型及可解释性研究",
        "stats": "## 📊 统计概览",
        "total": "论文总数", "core": "核心论文", "strong": "高相关论文",
        "monthly": "本月新增", "sources": "来源分布",
        "last_update": "最后更新",
        "top_cited": "## 🏆 高引用论文 Top 5",
        "rank": "排名", "citations": "引用数", "score": "分数",
        "latest_core": "## 🔥 最新核心论文",
        "strong_section": "## 📎 高相关论文",
        "year_label": "年", "papers_label": "篇",
        "tag": "标签", "summary": "摘要", "author": "作者",
        "no_core": "*暂无核心论文*", "no_strong": "*暂无高相关论文*",
        "full_list": "📄 **完整论文列表**: [ALL_PAPERS.md](ALL_PAPERS.md)",
        "auto_update": "## ⚙️ 自动更新",
        "auto_desc": "本项目通过 **GitHub Actions** 每天自动搜索 arXiv 最新论文，经评分筛选后入库。",
        "license": "## 📄 License",
        "license_text": "仅供学术研究使用",
        "all_title": "# 📚 完整论文列表",
        "all_subtitle": "> 最后更新: {now} | 共 {total} 篇",
        "query_type": "查询类型", "source_col": "来源",
        "lang_switch": "[English](README.md) | **中文**",
        "col_title": "标题",
        "year": "年份",
    },
    "en": {
        "title": "# 📚 Video CNN Interpretability Paper Library",
        "subtitle": "> Automated paper search & curation | Focused on 3DCNN, R(2+1)D models & interpretability research",
        "stats": "## 📊 Overview",
        "total": "Total Papers", "core": "Core Papers", "strong": "Strongly Related",
        "monthly": "New This Month", "sources": "Sources",
        "last_update": "Last Updated",
        "top_cited": "## 🏆 Top 5 Most Cited",
        "rank": "Rank", "citations": "Citations", "score": "Score",
        "latest_core": "## 🔥 Latest Core Papers",
        "strong_section": "## 📎 Strongly Related Papers",
        "year_label": "", "papers_label": "papers",
        "tag": "Tag", "summary": "Summary", "author": "Author",
        "no_core": "*No core papers yet*", "no_strong": "*No strongly related papers yet*",
        "full_list": "📄 **Full paper list**: [ALL_PAPERS.md](ALL_PAPERS.md)",
        "auto_update": "## ⚙️ Auto Update",
        "auto_desc": "This project uses **GitHub Actions** to search arXiv daily, score & filter papers before adding them to the index.",
        "license": "## 📄 License",
        "license_text": "For academic research use only",
        "all_title": "# 📚 Complete Paper List",
        "all_subtitle": "> Last updated: {now} | {total} papers total",
        "query_type": "Query Type", "source_col": "Source",
        "lang_switch": "**English** | [中文](README_zh.md)",
        "col_title": "Title",
        "year": "Year",
    },
}


def _t(lang: str, key: str) -> str:
    return _I18N.get(lang, _I18N["zh"]).get(key, key)


def generate_main_readme(records: list[dict], stats: dict, lang: str = "zh") -> str:
    """生成主 README，包含精选视图 + 年份折叠视图"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now_month = datetime.now().strftime("%Y-%m")
    total = stats.get("total", len(records))
    by_label = stats.get("by_label", {})
    core_count = by_label.get("core", 0)
    strong_count = by_label.get("strongly_related", 0)

    monthly_new = sum(
        1 for r in records if r.get("published", "").startswith(now_month)
    )

    # Top 5: core + strongly_related, sorted by sqrt(citation) * relevance
    cited_papers = [
        r for r in records
        if r.get("citation_count", 0) > 0
        and r.get("quality_label") in ("core", "strongly_related")
    ]
    cited_papers.sort(
        key=lambda r: -(r["citation_count"] ** 0.5 * r.get("relevance_score", 1))
    )
    top5_cited = cited_papers[:5]

    source_counts: dict[str, int] = defaultdict(int)
    for r in records:
        source_counts[r.get("source", "arxiv")] += 1
    arxiv_count = source_counts.get("arxiv", 0)
    ss_count = source_counts.get("semantic_scholar", 0)

    core_papers = [r for r in records if r.get("quality_label") == "core"]
    core_papers.sort(key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)))
    latest_core = core_papers[:20]

    strong_papers = [r for r in records if r.get("quality_label") == "strongly_related"]
    strong_papers.sort(key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)))
    latest_strong = strong_papers[:10]

    T = lambda k: _t(lang, k)
    summary_key = "summary_zh" if lang == "zh" else "one_line_summary"

    lines: list[str] = []
    # 语言切换
    lines.append(T("lang_switch"))
    lines.append("")
    lines.append(T("title"))
    lines.append("")
    lines.append(T("subtitle"))
    lines.append("")

    # 统计
    lines.append(T("stats"))
    lines.append("")
    lines.append(f"- **{T('total')}**: {total}")
    lines.append(f"- **{T('core')}**: {core_count}")
    lines.append(f"- **{T('strong')}**: {strong_count}")
    lines.append(f"- **{T('monthly')}**: {monthly_new}")
    if lang == "zh":
        lines.append(f"- **{T('sources')}**: arXiv {arxiv_count} 篇 | Semantic Scholar {ss_count} 篇")
    else:
        lines.append(f"- **{T('sources')}**: arXiv {arxiv_count} | Semantic Scholar {ss_count}")
    lines.append(f"- **{T('last_update')}**: {now}")
    lines.append("")

    # Top 5
    if top5_cited:
        lines.append(T("top_cited"))
        lines.append("")
        lines.append(f"| {T('rank')} | {T('col_title')} | {T('citations')} | {T('score')} |")
        lines.append("|------|------|--------|------|")
        for idx, p in enumerate(top5_cited, 1):
            title = p.get("title", "")[:60]
            citations = p.get("citation_count", 0)
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {idx} | [{title}]({url}) | {citations} | {score} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 最新核心论文
    lines.append(T("latest_core"))
    lines.append("")
    if latest_core:
        lines.append(f"| {T('year')} | {T('col_title')} | {T('summary')} | {T('author')} | {T('score')} |")
        lines.append("|------|------|------|------|------|")
        for p in latest_core:
            title = p.get("title", "")[:60]
            summary = p.get(summary_key, p.get("one_line_summary", ""))[:80]
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            year = p.get("year", "")
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {year} | [{title}]({url}) | {summary} | {authors} | {score} |")
    else:
        lines.append(T("no_core"))
    lines.append("")

    # 高相关论文
    lines.append(T("strong_section"))
    lines.append("")
    if latest_strong:
        lines.append(f"| {T('year')} | {T('col_title')} | {T('summary')} | {T('author')} | {T('score')} |")
        lines.append("|------|------|------|------|------|")
        for p in latest_strong:
            title = p.get("title", "")[:60]
            summary = p.get(summary_key, p.get("one_line_summary", ""))[:80]
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            year = p.get("year", "")
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {year} | [{title}]({url}) | {summary} | {authors} | {score} |")
    else:
        lines.append(T("no_strong"))
    lines.append("")
    lines.append("---")
    lines.append("")

    # 年份折叠视图
    by_year: dict[int, list[dict]] = defaultdict(list)
    for r in records:
        if r.get("quality_label") in ("core", "strongly_related", "weakly_related"):
            by_year[r.get("year", 0)].append(r)

    for year in sorted(by_year.keys(), reverse=True):
        year_papers = sorted(by_year[year], key=lambda r: -r.get("relevance_score", 0))
        label_icon = {"core": "🔥", "strongly_related": "📎", "weakly_related": "📝"}
        count = len(year_papers)
        if lang == "zh":
            lines.append(f"<details>")
            lines.append(f"<summary>📅 {year} 年 ({count} 篇)</summary>")
        else:
            lines.append(f"<details>")
            lines.append(f"<summary>📅 {year} ({count} papers)</summary>")
        lines.append("")
        lines.append(f"| {T('tag')} | {T('col_title')} | {T('summary')} | {T('author')} | {T('score')} |")
        lines.append("|------|------|------|------|------|")
        for p in year_papers:
            icon = label_icon.get(p.get("quality_label", ""), "📝")
            title = p.get("title", "")[:50]
            summary = p.get(summary_key, p.get("one_line_summary", ""))[:70]
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {icon} | [{title}]({url}) | {summary} | {authors} | {score} |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(T("full_list"))
    lines.append("")
    lines.append(T("auto_update"))
    lines.append("")
    lines.append(T("auto_desc"))
    lines.append("")
    lines.append(T("license"))
    lines.append("")
    lines.append(T("license_text"))
    lines.append("")

    return "\n".join(lines)


def generate_all_papers(records: list[dict], lang: str = "zh") -> str:
    """生成完整论文列表"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    T = lambda k: _t(lang, k)
    summary_key = "summary_zh" if lang == "zh" else "one_line_summary"

    lines: list[str] = []
    lines.append(T("all_title"))
    lines.append("")
    lines.append(T("all_subtitle").format(now=now, total=len(records)))
    lines.append("")
    lines.append("---")
    lines.append("")

    by_year: dict[int, list[dict]] = defaultdict(list)
    for r in records:
        by_year[r.get("year", 0)].append(r)

    label_icon = {"core": "🔥", "strongly_related": "📎", "weakly_related": "📝", "noise": "❌"}

    for year in sorted(by_year.keys(), reverse=True):
        year_papers = sorted(by_year[year], key=lambda r: -r.get("relevance_score", 0))
        count = len(year_papers)
        if lang == "zh":
            lines.append(f"## {year} 年 ({count} 篇)")
        else:
            lines.append(f"## {year} ({count} papers)")
        lines.append("")
        lines.append(f"| {T('tag')} | {T('col_title')} | {T('summary')} | {T('author')} | {T('score')} | {T('query_type')} | {T('source_col')} |")
        lines.append("|------|------|------|------|----------|------|--------|")
        for p in year_papers:
            icon = label_icon.get(p.get("quality_label", ""), "📝")
            title = p.get("title", "")[:60]
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            score = p.get("relevance_score", 0)
            qt = p.get("query_type", "")
            url = p.get("url", "#")
            source = p.get("source", "arxiv")
            summary = p.get(summary_key, p.get("one_line_summary", ""))[:60]
            lines.append(f"| {icon} | [{title}]({url}) | {summary} | {authors} | {score} | {qt} | {source} |")
        lines.append("")

    return "\n".join(lines)
