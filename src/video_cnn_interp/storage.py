"""JSONL 索引存储模块"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime


_ENRICHMENT_FIELDS = {
    "one_line_summary",
    "summary_zh",
    "method_type",
    "relation_to_r2plus1d",
    "mentions_r2plus1d",
    "r2plus1d_context",
    "topics",
}


def _is_empty(value) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _unique_history(items: list[dict]) -> list[dict]:
    seen: set[tuple[int, str]] = set()
    result: list[dict] = []
    for item in items:
        key = (int(item.get("version", 0)), str(item.get("updated", "")))
        if key in seen:
            continue
        seen.add(key)
        result.append({"version": key[0], "updated": key[1]})
    return result[-10:]


def merge_paper_records(existing: dict, incoming: dict) -> dict:
    """合并同一论文的两条记录，避免空值覆盖已增强字段。"""
    if not existing:
        result = dict(incoming)
        result["version_history"] = _unique_history(result.get("version_history", []))
        return result

    old_version = int(existing.get("version", 1) or 1)
    new_version = int(incoming.get("version", 1) or 1)
    result = dict(existing)

    if new_version >= old_version:
        for key, value in incoming.items():
            if key == "version_history":
                continue
            if key in _ENRICHMENT_FIELDS and _is_empty(value):
                continue
            if _is_empty(value) and not _is_empty(existing.get(key)):
                continue
            result[key] = value

    result["citation_count"] = max(
        int(existing.get("citation_count", 0) or 0),
        int(incoming.get("citation_count", 0) or 0),
    )
    if _is_empty(result.get("venue")) and not _is_empty(existing.get("venue")):
        result["venue"] = existing["venue"]

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
        result["sources"] = sources
        result["source"] = existing.get("source") or incoming.get("source") or sources[0]

    history = list(existing.get("version_history", []) or [])
    history.extend(incoming.get("version_history", []) or [])
    if new_version > old_version:
        history.append({"version": old_version, "updated": existing.get("updated", "")})
    result["version_history"] = _unique_history(history)
    return result


def _load_index(index_path: Path) -> dict[str, dict]:
    """加载现有索引，返回 {canonical_id: record}"""
    records: dict[str, dict] = {}
    if not index_path.exists():
        return records
    with index_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                cid = rec.get("canonical_id", "")
                if cid:
                    records[cid] = rec
            except json.JSONDecodeError as exc:
                raise ValueError(f"索引第 {line_number} 行不是有效 JSON: {index_path}") from exc
    return records


def _save_index(index_path: Path, records: dict[str, dict]) -> None:
    """将索引写回 JSONL 文件，按年份降序、分数降序排列"""
    sorted_recs = sorted(
        records.values(),
        key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)),
    )
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = index_path.with_suffix(index_path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in sorted_recs:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    temp_path.replace(index_path)


def load_index(index_path: str | Path) -> dict[str, dict]:
    """公开接口：加载索引"""
    return _load_index(Path(index_path))


def replace_index(index_path: str | Path, records: list[dict]) -> None:
    """使用完整数据集原子替换索引，供迁移与维护任务使用。"""
    by_id = {
        record["canonical_id"]: merge_paper_records({}, record)
        for record in records
        if record.get("canonical_id")
    }
    _save_index(Path(index_path), by_id)


def upsert_paper(index_path: str | Path, record: dict) -> bool:
    """插入或更新一篇论文到索引
    
    返回 True 表示新增，False 表示更新
    """
    p = Path(index_path)
    records = _load_index(p)
    cid = record.get("canonical_id", "")
    if not cid:
        return False

    is_new = cid not in records
    merged = merge_paper_records(records.get(cid, {}), record)
    if not is_new and merged == records[cid]:
        return False
    records[cid] = merged

    _save_index(p, records)
    return is_new


def batch_upsert(index_path: str | Path, records: list[dict]) -> tuple[int, int]:
    """批量写入，返回 (新增数, 更新数)"""
    new_count, update_count, _ = batch_upsert_detailed(index_path, records)
    return new_count, update_count


def batch_upsert_detailed(index_path: str | Path, records: list[dict]) -> tuple[int, int, int]:
    """批量写入，返回 (新增数, 实际更新数, 未变化数)。"""
    p = Path(index_path)
    existing = _load_index(p)
    new_count = 0
    update_count = 0
    unchanged_count = 0
    for rec in records:
        cid = rec.get("canonical_id", "")
        if not cid:
            continue
        if cid in existing:
            merged = merge_paper_records(existing[cid], rec)
            if merged == existing[cid]:
                unchanged_count += 1
            else:
                existing[cid] = merged
                update_count += 1
        else:
            existing[cid] = merge_paper_records({}, rec)
            new_count += 1
    if new_count or update_count or not p.exists():
        _save_index(p, existing)
    return new_count, update_count, unchanged_count


def get_existing_ids(index_path: str | Path) -> set[str]:
    """返回索引中所有 canonical_id 的集合"""
    return set(_load_index(Path(index_path)).keys())


def get_all_records(index_path: str | Path) -> list[dict]:
    """返回所有记录的列表，按年份降序、分数降序"""
    records = _load_index(Path(index_path))
    return sorted(
        records.values(),
        key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)),
    )


def get_stats(index_path: str | Path) -> dict:
    """返回索引统计信息"""
    records = _load_index(Path(index_path))
    total = len(records)
    by_label: dict[str, int] = {}
    by_year: dict[int, int] = {}
    for rec in records.values():
        label = rec.get("quality_label", "unknown")
        by_label[label] = by_label.get(label, 0) + 1
        year = rec.get("year", 0)
        by_year[year] = by_year.get(year, 0) + 1
    return {
        "total": total,
        "by_label": by_label,
        "by_year": dict(sorted(by_year.items(), reverse=True)),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
