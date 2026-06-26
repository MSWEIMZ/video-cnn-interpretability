"""统一 CLI 入口"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime

from .config import load_app_config
from .collector import collect_candidates
from .normalizer import build_paper_record, extract_year
from .scorer import compute_relevance_score, assign_quality_label
from .storage import upsert_paper, get_all_records, get_stats, get_existing_ids
from .readme import generate_main_readme, generate_all_papers
from .notify import send_daily_digest, send_error_alert


def run_daily(base_dir: str | Path | None = None) -> None:
    """每日主流程"""
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent
    base = Path(base_dir)
    config_path = base / "search_config.json"

    print("=" * 60)
    print("视频 CNN 可解释性论文搜索系统 v2.0")
    print("=" * 60)

    # 加载配置
    print("\n[1/6] 加载配置...")
    config = load_app_config(config_path)
    output_dir = base / config.runtime.output_dir
    index_path = output_dir / "index.jsonl"
    output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []

    # 收集候选论文
    print("\n[2/6] 搜索候选论文...")
    try:
        candidates = collect_candidates(config)
    except Exception as e:
        err_msg = f"搜索失败: {e}"
        print(f"  [ERROR] {err_msg}")
        errors.append(err_msg)
        send_error_alert(err_msg)
        return

    if not candidates:
        print("  未找到候选论文，跳过后续步骤")
        return

    # 评分与筛选
    print("\n[3/6] 评分与筛选...")
    existing_ids = get_existing_ids(index_path)
    new_records: list[dict] = []
    noise_blocked = 0
    years_from = config.filters.years_from
    years_to = config.filters.years_to

    for query_type, search_query, raw_paper in candidates:
        # 年份过滤
        arxiv_id = raw_paper.get("arxiv_id", "")
        published = raw_paper.get("published", "")
        year = extract_year(published, arxiv_id)
        if year < years_from or year > years_to:
            continue

        # 类别过滤
        categories = raw_paper.get("categories", [])
        allowed = set(config.filters.allowed_categories)
        if categories and not any(c in allowed for c in categories):
            # 如果没有任何 cs 类别，跳过
            if not any(c.startswith("cs.") for c in categories):
                continue

        # 计算分数
        score = compute_relevance_score(raw_paper, query_type, config)
        label = assign_quality_label(score, config)

        if label == "noise":
            noise_blocked += 1
            continue

        # 构建标准记录
        record = build_paper_record(raw_paper, query_type, search_query)
        record.relevance_score = score
        record.quality_label = label

        # Markdown 卡片
        if config.runtime.write_markdown_cards:
            md_dir = output_dir / str(record.year) / label
            md_dir.mkdir(parents=True, exist_ok=True)
            md_path = md_dir / f"{record.canonical_id}.md"
            _write_paper_card(md_path, record)
            record.markdown_path = str(md_path.relative_to(base))

        new_records.append(record.to_dict())

    print(f"  通过筛选: {len(new_records)} 篇")
    print(f"  噪声拦截: {noise_blocked} 篇")

    # 写入索引
    print("\n[4/6] 写入索引...")
    added = 0
    updated = 0
    for rec in new_records:
        is_new = upsert_paper(index_path, rec)
        if is_new:
            added += 1
        else:
            updated += 1
    print(f"  新增: {added} 篇 | 更新: {updated} 篇")

    # 生成 README
    print("\n[5/6] 生成 README...")
    if config.runtime.write_readme:
        all_records = get_all_records(index_path)
        stats = get_stats(index_path)
        stats["noise_blocked_today"] = noise_blocked

        readme_content = generate_main_readme(all_records, stats)
        readme_path = base / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        print(f"  README 已更新: {readme_path}")

        all_papers_content = generate_all_papers(all_records)
        all_papers_path = base / "ALL_PAPERS.md"
        all_papers_path.write_text(all_papers_content, encoding="utf-8")
        print(f"  ALL_PAPERS 已更新: {all_papers_path}")

    # 发送通知
    print("\n[6/6] 发送通知...")
    if config.runtime.notify_feishu:
        stats = get_stats(index_path)
        stats["noise_blocked_today"] = noise_blocked
        send_daily_digest(
            [{"quality_label": r.get("quality_label"), "title": r.get("title")} for r in new_records],
            stats,
            errors if errors else None,
        )

    print(f"\n✅ 完成！新增 {added} 篇，更新 {updated} 篇，噪声拦截 {noise_blocked} 篇")


def _write_paper_card(path: Path, record) -> None:
    """写入单篇论文 Markdown 卡片"""
    content = f"""# {record.title}

**作者**: {', '.join(record.authors[:5])}{'...' if len(record.authors) > 5 else ''}

**年份**: {record.year} | **分类**: {record.quality_label} | **分数**: {record.relevance_score}

**arXiv**: [{record.canonical_id}]({record.url})

**查询类型**: {record.query_type} | **查询词**: {record.search_query}

---

## 摘要

{record.abstract}

---

*自动整理于 {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    """CLI 入口"""
    if len(sys.argv) > 1 and sys.argv[1] == "run-daily":
        run_daily()
    else:
        print("用法: python -m video_cnn_interp.cli run-daily")
        sys.exit(1)


if __name__ == "__main__":
    main()
