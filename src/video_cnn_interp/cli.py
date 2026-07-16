"""unified CLI entry"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from .config import load_app_config
from .collector import collect_candidates
from .normalizer import build_paper_record, extract_year
from .scorer import compute_relevance_score, assign_quality_label, is_video_domain_relevant
from .storage import (
    batch_upsert_detailed,
    get_all_records,
    get_stats,
    load_index,
    merge_paper_records,
    replace_index,
)
from .readme import generate_main_readme, generate_all_papers
from .notify import send_daily_digest, send_error_alert
from .topics import classify_paper_topics, generate_topics_markdown
from .summarizer import enhance_record
from .dashboard import generate_dashboard_html
from .trends import generate_trends_markdown
from .sources.crossref import enrich_record as enrich_from_crossref
from .maintenance import repair_records


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

    print("\n[2/8] Collect candidates...")
    candidates = collect_candidates(config)

    if not candidates:
        print("  No candidates.")
        if config.runtime.notify_feishu:
            send_daily_digest([], get_stats(index_path))
        return

    print("\n[3/8] Score and filter...")
    existing_records = load_index(index_path)
    existing_ids = set(existing_records)
    accepted_records: list[dict] = []
    noise_blocked = 0
    domain_blocked = 0
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
            continue

        if not is_video_domain_relevant(raw_paper, config.filters.required_domain_keywords):
            domain_blocked += 1
            continue

        score = compute_relevance_score(raw_paper, query_type, config)
        label = assign_quality_label(score, config)
        if label == "noise":
            noise_blocked += 1
            continue

        normalized = build_paper_record(raw_paper, query_type, search_query).to_dict()
        normalized["relevance_score"] = score
        normalized["quality_label"] = label
        existing = existing_records.get(normalized["canonical_id"], {})
        merged = merge_paper_records(existing, normalized)
        merged = enhance_record(merged)
        merged["topics"] = classify_paper_topics(merged)
        if not merged.get("markdown_path"):
            md_path = output_dir / str(merged["year"]) / label / f"{merged['canonical_id']}.md"
            merged["markdown_path"] = str(md_path.relative_to(base))
        accepted_records.append(merged)

    print(f"  Passed: {len(accepted_records)}")
    print(f"  Noise blocked: {noise_blocked}")
    print(f"  Outside video domain: {domain_blocked}")

    truly_new = [r for r in accepted_records if r["canonical_id"] not in existing_ids]
    if config.runtime.crossref_enabled and truly_new:
        print("\n[3.5/8] Enrich new papers with CrossRef...")
        limit = config.runtime.crossref_max_new_per_run
        enriched_by_id = {
            record["canonical_id"]: enrich_from_crossref(record)
            for record in truly_new[:limit]
        }
        accepted_records = [enriched_by_id.get(r["canonical_id"], r) for r in accepted_records]

    print("\n[4/8] Write index...")
    added, updated, unchanged = batch_upsert_detailed(index_path, accepted_records)
    print(f"  added={added} updated={updated} unchanged={unchanged}")

    final_records_by_id = load_index(index_path)
    new_records = [final_records_by_id[r["canonical_id"]] for r in truly_new]
    if config.runtime.write_markdown_cards:
        for record in new_records:
            _write_paper_card(base / record["markdown_path"], record)

    print("\n[5/8] Generate README...")
    all_records = get_all_records(index_path)
    stats = get_stats(index_path)
    stats["noise_blocked_today"] = noise_blocked
    if config.runtime.write_readme:
        readme_zh = generate_main_readme(all_records, stats, lang="zh")
        (base / "README_zh.md").write_text(readme_zh, encoding="utf-8")
        readme_en = generate_main_readme(all_records, stats, lang="en")
        (base / "README.md").write_text(readme_en, encoding="utf-8")
        all_papers_en = generate_all_papers(all_records, lang="en")
        (base / "ALL_PAPERS.md").write_text(all_papers_en, encoding="utf-8")
        all_papers_zh = generate_all_papers(all_records, lang="zh")
        (base / "ALL_PAPERS_zh.md").write_text(all_papers_zh, encoding="utf-8")
        print("  README/ALL_PAPERS updated (zh + en)")

    print("\n[6/8] Enhancement already applied before storage.")

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
            None,
        )

    print(f"\n[DONE] added={added} updated={updated} noise_blocked={noise_blocked}")


def _write_paper_card(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    authors = record.get("authors", [])
    content = f"""# {record.get('title', '')}

**authors**: {', '.join(authors[:5])}{'...' if len(authors) > 5 else ''}

**year**: {record.get('year', '')} | **label**: {record.get('quality_label', '')} | **score**: {record.get('relevance_score', 0)}

**paper**: [{record.get('canonical_id', '')}]({record.get('url', '#')})

**query**: {record.get('query_type', '')} | {record.get('search_query', '')}

**中文导读**: {record.get('summary_zh', '')}

---

## abstract

{record.get('abstract', '')}

---

*automatically curated by Video CNN/XAI Research Hub*
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
    batch_upsert_detailed(index_path, all_records)

    stats = get_stats(index_path)
    readme_zh = generate_main_readme(all_records, stats, lang="zh")
    (base / "README_zh.md").write_text(readme_zh, encoding="utf-8")
    readme_en = generate_main_readme(all_records, stats, lang="en")
    (base / "README.md").write_text(readme_en, encoding="utf-8")
    all_papers_en = generate_all_papers(all_records, lang="en")
    (base / "ALL_PAPERS.md").write_text(all_papers_en, encoding="utf-8")
    all_papers_zh = generate_all_papers(all_records, lang="zh")
    (base / "ALL_PAPERS_zh.md").write_text(all_papers_zh, encoding="utf-8")
    (base / "TOPICS.md").write_text(generate_topics_markdown(all_records), encoding="utf-8")
    trends_content = generate_trends_markdown(all_records)
    (base / "TRENDS.md").write_text(trends_content, encoding="utf-8")
    (base / "dashboard.html").write_text(generate_dashboard_html(all_records, stats), encoding="utf-8")
    print("  All display files updated")

    print(f"DONE: enhanced={enhanced} rescored={rescored} total={len(all_records)}")


def _write_jsonl_atomic(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL 第 {line_number} 行无效: {path}") from exc
    return records


def _merge_quarantine(existing: list[dict], incoming: list[dict]) -> list[dict]:
    merged: dict[tuple[str, str], dict] = {}
    for record in [*existing, *incoming]:
        identity = str(record.get("canonical_id") or record.get("title") or "")
        reason = str(record.get("quarantine_reason", "unknown"))
        merged[(identity, reason)] = record
    return list(merged.values())


def _write_display_files(base: Path, records: list[dict], stats: dict) -> None:
    (base / "README_zh.md").write_text(
        generate_main_readme(records, stats, lang="zh"), encoding="utf-8"
    )
    (base / "README.md").write_text(
        generate_main_readme(records, stats, lang="en"), encoding="utf-8"
    )
    (base / "ALL_PAPERS.md").write_text(
        generate_all_papers(records, lang="en"), encoding="utf-8"
    )
    (base / "ALL_PAPERS_zh.md").write_text(
        generate_all_papers(records, lang="zh"), encoding="utf-8"
    )
    (base / "TOPICS.md").write_text(generate_topics_markdown(records), encoding="utf-8")
    (base / "TRENDS.md").write_text(generate_trends_markdown(records), encoding="utf-8")
    (base / "dashboard.html").write_text(
        generate_dashboard_html(records, stats), encoding="utf-8"
    )


def run_repair(base_dir: str | Path | None = None) -> dict[str, int]:
    """无损清洗主索引，将噪声和身份错误记录保存到隔离区。"""
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent
    base = Path(base_dir)
    config = load_app_config(base / "search_config.json")
    output_dir = base / config.runtime.output_dir
    index_path = output_dir / "index.jsonl"

    records = get_all_records(index_path)
    clean, quarantine, report = repair_records(records)
    curated: list[dict] = []
    for record in clean:
        if record.get("source") != "manual" and not is_video_domain_relevant(
            record, config.filters.required_domain_keywords
        ):
            rejected = dict(record)
            rejected["quarantine_reason"] = "outside_video_domain"
            quarantine.append(rejected)
            continue
        enhance_record(record)
        record["topics"] = classify_paper_topics(record)
        curated.append(record)

    clean = curated
    report["output"] = len(clean)
    report["quarantined"] = len(quarantine)

    quarantine_path = output_dir / "quarantine.jsonl"
    quarantine = _merge_quarantine(_read_jsonl(quarantine_path), quarantine)
    report["quarantined"] = len(quarantine)
    replace_index(index_path, clean)
    _write_jsonl_atomic(quarantine_path, quarantine)
    clean = get_all_records(index_path)
    stats = get_stats(index_path)
    _write_display_files(base, clean, stats)
    print(
        "Repair complete: "
        f"input={report['input']} output={report['output']} "
        f"quarantined={report['quarantined']} duplicates={report['duplicates_merged']}"
    )
    return report


def main() -> None:
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "run-daily":
            run_daily()
        elif len(sys.argv) > 1 and sys.argv[1] == "run-backfill":
            run_backfill()
        elif len(sys.argv) > 1 and sys.argv[1] == "run-repair":
            run_repair()
        else:
            print("usage: python -m video_cnn_interp.cli run-daily")
            print("       python -m video_cnn_interp.cli run-backfill")
            print("       python -m video_cnn_interp.cli run-repair")
            sys.exit(1)
    except Exception as exc:
        message = f"Paper pipeline failed: {exc}"
        print(f"[ERROR] {message}")
        send_error_alert(message)
        raise


if __name__ == "__main__":
    main()
