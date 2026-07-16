"""README 与 ALL_PAPERS 生成模块（支持中英文）"""
from __future__ import annotations
from datetime import datetime
from collections import defaultdict

# ── 语言包 ──────────────────────────────────────────────────────────────────
_I18N = {
    "zh": {
        "title": "# 📚 Video CNN/XAI Research Hub",
        "subtitle": "> 视频深度学习与可解释性论文自动搜集系统",
        "stats": "## 📊 统计概览",
        "total": "论文总数", "core": "核心论文", "strong": "高相关论文",
        "monthly": "本月新增", "sources": "来源分布",
        "last_update": "最后更新",
        "top_cited": "## 🏆 高影响力论文 Top 5",
        "rank": "排名", "citations": "引用数", "score": "分数",
        "latest_core": "## 🔥 最新核心论文",
        "trending": "## 🔥 近期热门",
        "trending_desc": "近两年高引用核心论文",
        "citations": "引用数",
        "strong_section": "## 📎 高相关论文",
        "year_label": "年", "papers_label": "篇",
        "tag": "标签", "summary": "摘要", "author": "作者",
        "no_core": "*暂无核心论文*", "no_strong": "*暂无高相关论文*",
        "full_list": "📄 **完整论文列表**: [ALL_PAPERS_zh.md](ALL_PAPERS_zh.md)",
        "auto_update": "## ⚙️ 自动更新",
        "auto_desc": "本项目通过 **GitHub Actions** 每天聚合 arXiv 与 Semantic Scholar，经规范化、去重、评分和 CrossRef 增强后入库。",
        "license": "## 📄 License",
        "license_text": "仅供学术研究使用",
        "all_title": "# 📚 完整论文列表 — Video CNN/XAI Research Hub",
        "all_subtitle": "> 最后更新: {now} | 共 {total} 篇",
        "query_type": "查询类型", "source_col": "来源",
        "lang_switch": "[English](README.md) | **中文**",
        "col_title": "标题",
        "year": "年份",
    },
    "en": {
        "title": "# 📚 Video CNN/XAI Research Hub",
        "subtitle": "> Automated paper curation for video deep learning & explainability research",
        "stats": "## 📊 Overview",
        "total": "Total Papers", "core": "Core Papers", "strong": "Strongly Related",
        "monthly": "New This Month", "sources": "Sources",
        "last_update": "Last Updated",
        "top_cited": "## 🏆 Top 5 Most Influential",
        "rank": "Rank", "citations": "Citations", "score": "Score",
        "latest_core": "## 🔥 Latest Core Papers",
        "trending": "## 🔥 Latest Trending",
        "trending_desc": "Top cited core papers from recent years",
        "citations": "Citations",
        "strong_section": "## 📎 Strongly Related Papers",
        "year_label": "", "papers_label": "papers",
        "tag": "Tag", "summary": "Summary", "author": "Author",
        "no_core": "*No core papers yet*", "no_strong": "*No strongly related papers yet*",
        "full_list": "📄 **Full paper list**: [ALL_PAPERS.md](ALL_PAPERS.md)",
        "auto_update": "## ⚙️ Auto Update",
        "auto_desc": "GitHub Actions aggregates arXiv and Semantic Scholar daily, then normalizes, deduplicates, scores, and enriches accepted papers with CrossRef.",
        "license": "## 📄 License",
        "license_text": "For academic research use only",
        "all_title": "# 📚 Complete Paper List — Video CNN/XAI Research Hub",
        "all_subtitle": "> Last updated: {now} | {total} papers total",
        "query_type": "Query Type", "source_col": "Source",
        "lang_switch": "**English** | [中文](README_zh.md)",
        "col_title": "Title",
        "year": "Year",
    },
}


def _t(lang: str, key: str) -> str:
    return _I18N.get(lang, _I18N["zh"]).get(key, key)


def _md_cell(value, limit: int | None = None) -> str:
    """转义 Markdown 表格单元格中的控制字符。"""
    text = str(value or "").replace("\r", " ").replace("\n", " ")
    if limit is not None:
        text = text[:limit]
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def generate_main_readme(records: list[dict], stats: dict, lang: str = "zh") -> str:
    """生成主 README，包含精选视图 + 年份折叠视图"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now_month = datetime.now().strftime("%Y-%m")
    current_year = datetime.now().year
    trending_start_year = current_year - 2
    total = stats.get("total", len(records))
    by_label = stats.get("by_label", {})
    core_count = by_label.get("core", 0)
    strong_count = by_label.get("strongly_related", 0)

    monthly_new = sum(
        1 for r in records if r.get("published", "").startswith(now_month)
    )

    # Top 5: 仅核心论文，避免通用高引用论文挤占主题相关结果。
    cited_papers = [
        r for r in records
        if r.get("citation_count", 0) > 0
        and r.get("quality_label") == "core"
    ]
    cited_papers.sort(
        key=lambda r: -(r["citation_count"] ** 0.5 * r.get("relevance_score", 1))
    )
    top5_cited = cited_papers[:5]

    source_counts: dict[str, int] = defaultdict(int)
    for r in records:
        source_counts[r.get("source") or "unknown"] += 1
    arxiv_count = source_counts.get("arxiv", 0)
    ss_count = source_counts.get("semantic_scholar", 0)
    manual_count = source_counts.get("manual", 0)
    unknown_count = source_counts.get("unknown", 0)
    crossref_count = sum(1 for r in records if "crossref" in (r.get("sources", []) or []))

    core_papers = [r for r in records if r.get("quality_label") == "core"]
    core_papers.sort(key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)))
    latest_core = core_papers[:20]

    strong_papers = [r for r in records if r.get("quality_label") == "strongly_related"]
    strong_papers.sort(key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)))
    latest_strong = strong_papers[:10]

    T = lambda k: _t(lang, k)
    summary_key = "summary_zh" if lang == "zh" else "one_line_summary"

    lines: list[str] = []
    
    # ── Language Switch ──
    lines.append(T("lang_switch"))
    lines.append("")
    
    # ── Hero Section (centered) ──
    lines.append('<h1 align="center">📚 Video CNN/XAI Research Hub</h1>')
    lines.append(f'<p align="center"><em>{T("subtitle").replace("> ", "")}</em></p>')
    lines.append("")
    
    # ── Badges ──
    lines.append('<p align="center">')
    lines.append(f'  <img src="https://img.shields.io/badge/papers-{total}-blue" alt="papers" />')
    lines.append(f'  <img src="https://img.shields.io/badge/core-{core_count}-green" alt="core" />')
    lines.append(f'  <img src="https://img.shields.io/badge/strongly_related-{strong_count}-yellow" alt="strongly_related" />')
    lines.append(f'  <img src="https://img.shields.io/badge/arXiv-{arxiv_count}-critical" alt="arXiv" />')
    lines.append(f'  <img src="https://img.shields.io/badge/Semantic_Scholar-{ss_count}-blueviolet" alt="Semantic Scholar" />')
    lines.append(f'  <img src="https://img.shields.io/badge/last_update-{now[:10]}-orange" alt="last_update" />')
    lines.append('  <img src="https://img.shields.io/badge/license-academic--only-lightgrey" alt="license" />')
    lines.append('</p>')
    lines.append("")
    
    # ── Quick Navigation ──
    lines.append("---")
    lines.append("")
    if lang == "zh":
        lines.append(
            "**快速导航** · [🏆 高影响力](#-高影响力论文-top-5) · "
            f"[🔥 近期热门](#-近期热门-{trending_start_year}-{current_year}) · "
            "[📄 核心论文](#-最新核心论文) · [📎 高相关](#-高相关论文) · "
            "[🏷️ 主题](TOPICS.md) · [📈 趋势](TRENDS.md) · "
            "[🖥️ 看板](dashboard.html) · [📋 完整列表](ALL_PAPERS_zh.md)"
        )
    else:
        lines.append(
            "**Quick Navigation** · [🏆 Influential](#-top-5-most-influential) · "
            f"[🔥 Trending](#-latest-trending-{trending_start_year}-{current_year}) · "
            "[📄 Core](#-latest-core-papers) · [📎 Strongly Related](#-strongly-related-papers) · "
            "[🏷️ Topics](TOPICS.md) · [📈 Trends](TRENDS.md) · "
            "[🖥️ Dashboard](dashboard.html) · [📋 Full List](ALL_PAPERS.md)"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Stats Section ──
    lines.append(T("stats"))
    lines.append("")
    if lang == "zh":
        lines.append(f"| 指标 | 数量 |")
        lines.append(f"|------|------|")
        lines.append(f"| 📚 {T('total')} | **{total}** |")
        lines.append(f"| 🔥 {T('core')} | **{core_count}** |")
        lines.append(f"| 📎 {T('strong')} | **{strong_count}** |")
        lines.append(f"| 🆕 {T('monthly')} | **{monthly_new}** |")
        lines.append(f"| 📡 arXiv | {arxiv_count} |")
        lines.append(f"| 🔬 Semantic Scholar | {ss_count} |")
        lines.append(f"| 🔗 CrossRef 增强 | {crossref_count} |")
        lines.append(f"| ✍️ 手工整理 | {manual_count} |")
        if unknown_count:
            lines.append(f"| ❓ 来源待修复 | {unknown_count} |")
        lines.append(f"| ⏰ {T('last_update')} | {now} |")
    else:
        lines.append(f"| Metric | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| 📚 {T('total')} | **{total}** |")
        lines.append(f"| 🔥 {T('core')} | **{core_count}** |")
        lines.append(f"| 📎 {T('strong')} | **{strong_count}** |")
        lines.append(f"| 🆕 {T('monthly')} | **{monthly_new}** |")
        lines.append(f"| 📡 arXiv | {arxiv_count} |")
        lines.append(f"| 🔬 Semantic Scholar | {ss_count} |")
        lines.append(f"| 🔗 CrossRef Enriched | {crossref_count} |")
        lines.append(f"| ✍️ Manual | {manual_count} |")
        if unknown_count:
            lines.append(f"| ❓ Unknown Source | {unknown_count} |")
        lines.append(f"| ⏰ {T('last_update')} | {now} |")
    lines.append("")

    # Top 5
    if top5_cited:
        lines.append(T("top_cited"))
        lines.append("")
        lines.append(
            "> 该榜单强调长期学术影响；关注新论文请查看下方“近期热门”。"
            if lang == "zh"
            else "> This list highlights long-term impact; see Trending for recent work."
        )
        lines.append("")
        lines.append(f"| {T('rank')} | {T('col_title')} | {T('citations')} | {T('score')} |")
        lines.append("|------|------|--------|------|")
        for idx, p in enumerate(top5_cited, 1):
            title = _md_cell(p.get("title", ""), 60)
            citations = p.get("citation_count", 0)
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {idx} | [{title}]({url}) | {citations} | {score} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 近期热门（动态最近三年）
    trending = [
        r for r in records
        if r.get("quality_label") == "core"
        and r.get("year", 0) >= trending_start_year
        and r.get("citation_count", 0) > 0
    ]
    trending.sort(key=lambda r: -r["citation_count"])
    trending_top = trending[:5]

    lines.append(f"{T('trending')} ({trending_start_year}-{current_year})")
    lines.append("")
    if trending_top:
        lines.append(f"| {T('year')} | {T('col_title')} | {T('summary')} | {T('citations')} | {T('score')} |")
        lines.append("|------|------|------|--------|------|")
        for p in trending_top:
            title = _md_cell(p.get("title", ""), 60)
            summary = _md_cell(p.get(summary_key, p.get("one_line_summary", "")), 80)
            citations = p.get("citation_count", 0)
            year = p.get("year", "")
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {year} | [{title}]({url}) | {summary} | {citations} | {score} |")
    else:
        lines.append(T("no_core"))
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
            title = _md_cell(p.get("title", ""), 60)
            summary = _md_cell(p.get(summary_key, p.get("one_line_summary", "")), 80)
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            authors = _md_cell(authors)
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
            title = _md_cell(p.get("title", ""), 60)
            summary = _md_cell(p.get(summary_key, p.get("one_line_summary", "")), 80)
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            authors = _md_cell(authors)
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
        for p in year_papers[:12]:
            icon = label_icon.get(p.get("quality_label", ""), "📝")
            title = _md_cell(p.get("title", ""), 50)
            summary = _md_cell(p.get(summary_key, p.get("one_line_summary", "")), 70)
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            authors = _md_cell(authors)
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {icon} | [{title}]({url}) | {summary} | {authors} | {score} |")
        lines.append("")
        if len(year_papers) > 12:
            if lang == "zh":
                lines.append(f"*仅展示前 12 篇，完整 {len(year_papers)} 篇请查看 [ALL_PAPERS_zh.md](ALL_PAPERS_zh.md)。*")
            else:
                lines.append(f"*Showing 12 of {len(year_papers)} papers. See [ALL_PAPERS.md](ALL_PAPERS.md) for all entries.*")
            lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(T("full_list"))
    lines.append("")
    
    # ── Architecture ──
    if lang == "zh":
        lines.append("## 🏗️ 系统架构")
        lines.append("")
        lines.append("```")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                    search_config.json                       │")
        lines.append("│              (24 条查询 × 3 层深度)                         │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("                            ▼")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                     Collector                               │")
        lines.append("│         arXiv API  +  Semantic Scholar API                  │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("                            ▼")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│              Normalizer + CrossRef Enrichment               │")
        lines.append("│        ID/版本规范化、跨源去重、引用与 Venue 增强           │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("                            ▼")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                      Scorer                                 │")
        lines.append("│    关键词匹配 + 引用量 + Venue + 综述加分                   │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("                            ▼")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                      Storage                                │")
        lines.append("│   papers/index.jsonl + papers/quarantine.jsonl              │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("          ┌─────────────────┼─────────────────┐")
        lines.append("          ▼                 ▼                 ▼")
        lines.append("    ┌──────────┐     ┌──────────┐     ┌──────────┐")
        lines.append("    │ README   │     │ 飞书通知  │     │ Dashboard │")
        lines.append("    │ (展示层) │     │ (推送层)  │     │ (看板层)  │")
        lines.append("    └──────────┘     └──────────┘     └──────────┘")
        lines.append("```")
    else:
        lines.append("## 🏗️ Architecture")
        lines.append("")
        lines.append("```")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                    search_config.json                       │")
        lines.append("│              (24 queries × 3 depth layers)                  │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("                            ▼")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                     Collector                               │")
        lines.append("│         arXiv API  +  Semantic Scholar API                  │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("                            ▼")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│              Normalizer + CrossRef Enrichment               │")
        lines.append("│        ID/version normalization, dedup, citations           │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("                            ▼")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                      Scorer                                 │")
        lines.append("│    Keyword Match + Citations + Venue + Survey Bonus          │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("                            ▼")
        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                      Storage                                │")
        lines.append("│   papers/index.jsonl + papers/quarantine.jsonl              │")
        lines.append("└───────────────────────────┬─────────────────────────────────┘")
        lines.append("                            │")
        lines.append("          ┌─────────────────┼─────────────────┐")
        lines.append("          ▼                 ▼                 ▼")
        lines.append("    ┌──────────┐     ┌──────────┐     ┌──────────┐")
        lines.append("    │ README   │     │ Feishu   │     │ Dashboard │")
        lines.append("    │ (Display)│     │ (Notify) │     │  (HTML)   │")
        lines.append("    └──────────┘     └──────────┘     └──────────┘")
        lines.append("```")
    lines.append("")
    
    # ── Features ──
    if lang == "zh":
        lines.append("## ✨ 核心特性")
        lines.append("")
        lines.append("| 🎯 智能搜索 | 📊 数据增强 | 🌐 多源聚合 | 🔔 自动通知 |")
        lines.append("|:----------:|:----------:|:----------:|:----------:|")
        lines.append("| 每日自动搜索 arXiv | CrossRef 引用回填 | arXiv + Semantic Scholar | 飞书 Webhook |")
        lines.append("| 24 条分层查询 | 中英文摘要生成 | 标题去重 + ID 规范化 | 成功/失败通知 |")
        lines.append("| 评分筛选入库 | 主题聚类分析 | 引用量 + Venue 增强 | GitHub Actions |")
    else:
        lines.append("## ✨ Features")
        lines.append("")
        lines.append("| 🎯 Smart Search | 📊 Data Enhancement | 🌐 Multi-Source | 🔔 Auto Notify |")
        lines.append("|:--------------:|:------------------:|:--------------:|:--------------:|")
        lines.append("| Daily arXiv search | CrossRef enrichment for new papers | arXiv + Semantic Scholar | Feishu Webhook |")
        lines.append("| 24 layered queries | CN/EN summary generation | Title dedup + ID norm | Success/Failure alerts |")
        lines.append("| Score-based filtering | Topic clustering | Citation + Venue boost | GitHub Actions |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # ── Auto Update ──
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
            title = _md_cell(p.get("title", ""), 60)
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            score = p.get("relevance_score", 0)
            authors = _md_cell(authors)
            qt = _md_cell(p.get("query_type", ""))
            url = p.get("url", "#")
            source = _md_cell(p.get("source", "unknown"))
            summary = _md_cell(p.get(summary_key, p.get("one_line_summary", "")), 60)
            lines.append(f"| {icon} | [{title}]({url}) | {summary} | {authors} | {score} | {qt} | {source} |")
        lines.append("")

    return "\n".join(lines)
