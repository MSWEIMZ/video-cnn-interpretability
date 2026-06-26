"""趋势报告模块 - 生成月度/季度论文趋势分析"""
from __future__ import annotations
from datetime import datetime
from collections import defaultdict


def _quarter_from_month(month: int) -> str:
    """将月份转换为季度标识 Q1-Q4"""
    if month <= 3:
        return "Q1"
    elif month <= 6:
        return "Q2"
    elif month <= 9:
        return "Q3"
    else:
        return "Q4"


def _parse_published_date(published: str) -> tuple[int, int]:
    """从 published 字符串解析 (year, month)，解析失败返回 (0, 0)"""
    if not published or len(published) < 7:
        return (0, 0)
    try:
        year = int(published[:4])
        month = int(published[5:7])
        return (year, month)
    except (ValueError, IndexError):
        return (0, 0)


def _stats_to_table(rows: list[tuple[str, int]], header_label: str) -> list[str]:
    """将统计行转换为 Markdown 表格"""
    lines: list[str] = []
    if not rows:
        lines.append("*无数据*")
        return lines
    lines.append(f"| {header_label} | 数量 |")
    lines.append("|------|------|")
    for label, count in rows:
        lines.append(f"| {label} | {count} |")
    return lines


def generate_trends_markdown(records: list[dict]) -> str:
    """生成趋势报告 Markdown
    
    包含：
    - 按年份+季度统计论文数量
    - 按主题/方法类型统计趋势
    - 按来源统计
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------- 按年份+季度统计 ----------
    quarter_counts: dict[str, int] = defaultdict(int)
    for r in records:
        published = r.get("published", "")
        year, month = _parse_published_date(published)
        if year > 0 and month > 0:
            q = _quarter_from_month(month)
            key = f"{year} {q}"
            quarter_counts[key] += 1

    # ---------- 按主题统计 ----------
    topic_counts: dict[str, int] = defaultdict(int)
    for r in records:
        topics = r.get("topics", [])
        if isinstance(topics, list):
            for t in topics:
                topic_counts[str(t)] += 1
        elif isinstance(topics, str) and topics:
            topic_counts[topics] += 1

    # ---------- 按来源统计 ----------
    source_counts: dict[str, int] = defaultdict(int)
    for r in records:
        source_counts[r.get("source", "arxiv")] += 1

    # ---------- 按 method_type 统计 ----------
    method_counts: dict[str, int] = defaultdict(int)
    for r in records:
        mt = r.get("method_type", "other")
        if mt:
            for single_mt in mt.split(","):
                method_counts[single_mt.strip()] += 1

    # ---------- 生成 Markdown ----------
    lines: list[str] = []
    lines.append("# 📈 论文趋势报告")
    lines.append("")
    lines.append(f"> 生成时间: {now} | 共 {len(records)} 篇论文")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 年份+季度
    lines.append("## 📅 年度/季度论文数量")
    lines.append("")
    sorted_quarters = sorted(quarter_counts.items(), key=lambda x: x[0], reverse=True)
    lines.extend(_stats_to_table(sorted_quarters, "季度"))
    lines.append("")
    lines.append("---")
    lines.append("")

    # 主题分布
    lines.append("## 🏷️ 主题分布")
    lines.append("")
    sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])[:20]
    lines.extend(_stats_to_table(sorted_topics, "主题"))
    lines.append("")
    lines.append("---")
    lines.append("")

    # 方法类型
    lines.append("## 🔬 方法类型分布")
    lines.append("")
    sorted_methods = sorted(method_counts.items(), key=lambda x: -x[1])
    lines.extend(_stats_to_table(sorted_methods, "方法类型"))
    lines.append("")
    lines.append("---")
    lines.append("")

    # 来源分布
    lines.append("## 🌐 来源分布")
    lines.append("")
    sorted_sources = sorted(source_counts.items(), key=lambda x: -x[1])
    lines.extend(_stats_to_table(sorted_sources, "来源"))
    lines.append("")

    return "\n".join(lines)
