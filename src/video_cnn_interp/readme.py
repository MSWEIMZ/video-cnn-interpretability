"""README 与 ALL_PAPERS 生成模块"""
from __future__ import annotations
from datetime import datetime
from collections import defaultdict


def generate_main_readme(records: list[dict], stats: dict) -> str:
    """生成主 README，包含精选视图 + 年份折叠视图"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = stats.get("total", len(records))
    by_label = stats.get("by_label", {})
    core_count = by_label.get("core", 0)
    strong_count = by_label.get("strongly_related", 0)

    # 精选区：最新核心论文 top 20
    core_papers = [r for r in records if r.get("quality_label") == "core"]
    core_papers.sort(key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)))
    latest_core = core_papers[:20]

    # 高相关论文 top 10
    strong_papers = [r for r in records if r.get("quality_label") == "strongly_related"]
    strong_papers.sort(key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)))
    latest_strong = strong_papers[:10]

    lines: list[str] = []
    lines.append("# 📚 视频 CNN 可解释性论文库")
    lines.append("")
    lines.append("> 自动化论文搜索与整理系统 | 专注于 3DCNN、R(2+1)D 模型及可解释性研究")
    lines.append("")
    lines.append("## 📊 统计概览")
    lines.append("")
    lines.append(f"- **论文总数**: {total} 篇")
    lines.append(f"- **核心论文**: {core_count} 篇")
    lines.append(f"- **高相关论文**: {strong_count} 篇")
    lines.append(f"- **最后更新**: {now}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 最新核心论文
    lines.append("## 🔥 最新核心论文")
    lines.append("")
    if latest_core:
        lines.append("| 年份 | 标题 | 作者 | 分数 |")
        lines.append("|------|------|------|------|")
        for p in latest_core:
            title = p.get("title", "")[:60]
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            year = p.get("year", "")
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {year} | [{title}]({url}) | {authors} | {score} |")
    else:
        lines.append("*暂无核心论文*")
    lines.append("")

    # 高相关论文
    lines.append("## 📎 高相关论文")
    lines.append("")
    if latest_strong:
        lines.append("| 年份 | 标题 | 作者 | 分数 |")
        lines.append("|------|------|------|------|")
        for p in latest_strong:
            title = p.get("title", "")[:60]
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            year = p.get("year", "")
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {year} | [{title}]({url}) | {authors} | {score} |")
    else:
        lines.append("*暂无高相关论文*")
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
        lines.append(f"<details>")
        lines.append(f"<summary>📅 {year} 年 ({len(year_papers)} 篇)</summary>")
        lines.append("")
        lines.append("| 标签 | 标题 | 作者 | 分数 |")
        lines.append("|------|------|------|------|")
        for p in year_papers:
            icon = label_icon.get(p.get("quality_label", ""), "📝")
            title = p.get("title", "")[:60]
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            score = p.get("relevance_score", 0)
            url = p.get("url", "#")
            lines.append(f"| {icon} | [{title}]({url}) | {authors} | {score} |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("📄 **完整论文列表**: [ALL_PAPERS.md](ALL_PAPERS.md)")
    lines.append("")
    lines.append("## ⚙️ 自动更新")
    lines.append("")
    lines.append("本项目通过 **GitHub Actions** 每天自动搜索 arXiv 最新论文，经评分筛选后入库。")
    lines.append("")
    lines.append("## 📄 License")
    lines.append("")
    lines.append("仅供学术研究使用")
    lines.append("")

    return "\n".join(lines)


def generate_all_papers(records: list[dict]) -> str:
    """生成完整论文列表"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    lines.append("# 📚 完整论文列表")
    lines.append("")
    lines.append(f"> 最后更新: {now} | 共 {len(records)} 篇")
    lines.append("")
    lines.append("---")
    lines.append("")

    by_year: dict[int, list[dict]] = defaultdict(list)
    for r in records:
        by_year[r.get("year", 0)].append(r)

    label_icon = {"core": "🔥", "strongly_related": "📎", "weakly_related": "📝", "noise": "❌"}

    for year in sorted(by_year.keys(), reverse=True):
        year_papers = sorted(by_year[year], key=lambda r: -r.get("relevance_score", 0))
        lines.append(f"## {year} 年 ({len(year_papers)} 篇)")
        lines.append("")
        lines.append("| 标签 | 标题 | 作者 | 分数 | 查询类型 |")
        lines.append("|------|------|------|------|----------|")
        for p in year_papers:
            icon = label_icon.get(p.get("quality_label", ""), "📝")
            title = p.get("title", "")[:60]
            authors = ", ".join(p.get("authors", [])[:2])
            if len(p.get("authors", [])) > 2:
                authors += "+"
            score = p.get("relevance_score", 0)
            qt = p.get("query_type", "")
            url = p.get("url", "#")
            lines.append(f"| {icon} | [{title}]({url}) | {authors} | {score} | {qt} |")
        lines.append("")

    return "\n".join(lines)
