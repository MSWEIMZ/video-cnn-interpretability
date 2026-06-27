"""unified CLI entry"""
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
from .topics import classify_paper_topics, generate_topics_markdown
from .summarizer import enhance_record
from .dashboard import generate_dashboard_html
from .trends import generate_trends_markdown


def run_daily(base_dir: str | Path | None = None) -> None:
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent
    base = Path(base_dir)
    config_path = base / "search_config.json"

    print("=" * 60)
    print("Video CNN Interpretability Paper Search v2.0")
    print("=" * 60)

    print("\n[1/8] Load config...")
    config = load_app_config(config_path)
    output_dir = base / config.runtime.output_dir
    index_path = output_dir / "index.jsonl"
    output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []

    print("\n[2/8] Collect candidates...")
    try:
        candidates = collect_candidates(config)
    except Exception as e:
        err_msg = f"Search failed: {e}"
        print(f"  [ERROR] {err_msg}")
        errors.append(err_msg)
        send_error_alert(err_msg)
        return

    if not candidates:
        print("  No candidates, stop.")
        return

    print("\n[3/8] Score and filter...")
    existing_ids = get_existing_ids(index_path)
    new_records: list[dict] = []
    noise_blocked = 0
    years_from = config.filters.years_from
    years_to = config.filters.years_to

    for query_type, search_query, raw_paper in candidates:
        arxiv_id = raw_paper.get("arxiv_id", "")
        published = raw_paper.get("published", "")
        year = extract_year(published, arxiv_id)
        if year < years_from or year > years_to:
            continue

        categories = raw_paper.get("categories", [])
        allowed = set(config.filters.allowed_categories)
        if categories and not any(c in allowed for c in categories):
            if not any(c.startswith("cs.") for c in categories):
                continue

        score = compute_relevance_score(raw_paper, query_type, config)
        label = assign_quality_label(score, config)
        if label == "noise":
            noise_blocked += 1
            continue

        record = build_paper_record(raw_paper, query_type, search_query)
        record.relevance_score = score
        record.quality_label = label

        if config.runtime.write_markdown_cards:
            md_dir = output_dir / str(record.year) / label
            md_dir.mkdir(parents=True, exist_ok=True)
            md_path = md_dir / f"{record.canonical_id}.md"
            _write_paper_card(md_path, record)
            record.markdown_path = str(md_path.relative_to(base))

        new_records.append(record.to_dict())

    print(f"  Passed: {len(new_records)}")
    print(f"  Noise blocked: {noise_blocked}")

    print("\n[4/8] Write index...")
    added = 0
    updated = 0
    for rec in new_records:
        is_new = upsert_paper(index_path, rec)
        if is_new:
            added += 1
        else:
            updated += 1
    print(f"  added={added} updated={updated}")

    print("\n[5/8] Generate README...")
    all_records = get_all_records(index_path)
    stats = get_stats(index_path)
    stats["noise_blocked_today"] = noise_blocked
    if config.runtime.write_readme:
        readme_content = generate_main_readme(all_records, stats)
        (base / "README.md").write_text(readme_content, encoding="utf-8")
        all_papers_content = generate_all_papers(all_records)
        (base / "ALL_PAPERS.md").write_text(all_papers_content, encoding="utf-8")
        print("  README/ALL_PAPERS updated")

    print("\n[6/8] Enhance + topics...")
    all_records = [enhance_record(r) for r in all_records]
    for rec in all_records:
        rec["topics"] = classify_paper_topics(rec)
        upsert_paper(index_path, rec)

    print("\n[6.5/8] Generate trends report...")
    trends_content = generate_trends_markdown(all_records)
    (base / "TRENDS.md").write_text(trends_content, encoding="utf-8")
    print("  TRENDS.md updated")

    print("\n[7/8] Generate topics + dashboard...")
    (base / "TOPICS.md").write_text(generate_topics_markdown(all_records), encoding="utf-8")
    (base / "dashboard.html").write_text(generate_dashboard_html(all_records, stats), encoding="utf-8")
    print("  TOPICS.md / dashboard.html updated")

    print("\n[8/8] Notify...")
    if config.runtime.notify_feishu:
        send_daily_digest(
            [{
                "quality_label": r.get("quality_label"),
                "title": r.get("title"),
                "authors": r.get("authors", []),
                "url": r.get("url", ""),
                "relevance_score": r.get("relevance_score", 0),
                "citation_count": r.get("citation_count", 0),
                "venue": r.get("venue", ""),
                "summary_zh": r.get("summary_zh", ""),
            } for r in new_records],
            stats,
            errors or None,
        )

    print(f"\n[DONE] added={added} updated={updated} noise_blocked={noise_blocked}")


def _write_paper_card(path: Path, record) -> None:
    content = f"""# {record.title}

**authors**: {', '.join(record.authors[:5])}{'...' if len(record.authors) > 5 else ''}

**year**: {record.year} | **label**: {record.quality_label} | **score**: {record.relevance_score}

**arXiv**: [{record.canonical_id}]({record.url})

**query**: {record.query_type} | {record.search_query}

---

## abstract

{record.abstract}

---

*generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    path.write_text(content, encoding="utf-8")


def run_backfill(base_dir: str | Path | None = None) -> None:
    """回填现有论文的增强字段（summary_zh, method_type, topics, citation_count 等）"""
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent
    base = Path(base_dir)
    config_path = base / "search_config.json"

    print("=" * 60)
    print("Backfill: re-process existing papers")
    print("=" * 60)

    config = load_app_config(config_path)
    output_dir = base / config.runtime.output_dir
    index_path = output_dir / "index.jsonl"

    if not index_path.exists():
        print("  [ERROR] index.jsonl does not exist, run run-daily first")
        return

    all_records = get_all_records(index_path)
    print(f"Loaded existing papers: {len(all_records)}")

    print("Enhance fields (summary_zh, method_type, topics, r2plus1d)...")
    enhanced = 0
    for rec in all_records:
        old_summary = rec.get("summary_zh", "")
        old_method = rec.get("method_type", "other")
        rec = enhance_record(rec)
        rec["topics"] = classify_paper_topics(rec)
        if rec.get("summary_zh", "") != old_summary or rec.get("method_type", "other") != old_method:
            enhanced += 1
    print(f"  Enhanced {enhanced} papers")

    print("Re-scoring...")
    rescored = 0
    for rec in all_records:
        old_score = rec.get("relevance_score", 0)
        old_label = rec.get("quality_label", "")
        query_type = rec.get("query_type", "core")
        score = compute_relevance_score(rec, query_type, config)
        label = assign_quality_label(score, config)
        rec["relevance_score"] = score
        rec["quality_label"] = label
        if score != old_score or label != old_label:
            rescored += 1
    print(f"  Re-scored {rescored} papers")

    print("Write back index + regenerate display files...")
    for rec in all_records:
        upsert_paper(index_path, rec)

    stats = get_stats(index_path)
    readme_content = generate_main_readme(all_records, stats)
    (base / "README.md").write_text(readme_content, encoding="utf-8")
    all_papers_content = generate_all_papers(all_records)
    (base / "ALL_PAPERS.md").write_text(all_papers_content, encoding="utf-8")
    (base / "TOPICS.md").write_text(generate_topics_markdown(all_records), encoding="utf-8")
    trends_content = generate_trends_markdown(all_records)
    (base / "TRENDS.md").write_text(trends_content, encoding="utf-8")
    (base / "dashboard.html").write_text(generate_dashboard_html(all_records, stats), encoding="utf-8")
    print("  All display files updated")

    print(f"DONE: enhanced={enhanced} rescored={rescored} total={len(all_records)}")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "run-daily":
        run_daily()
    elif len(sys.argv) > 1 and sys.argv[1] == "run-backfill":
        run_backfill()
    else:
        print("usage: python -m video_cnn_interp.cli run-daily")
        print("       python -m video_cnn_interp.cli run-backfill")
        sys.exit(1)


if __name__ == "__main__":
    main()
