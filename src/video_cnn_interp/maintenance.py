"""索引审计与无损修复。"""
from __future__ import annotations

import re
from collections import OrderedDict

from .storage import merge_paper_records


_CLASSIC_IDENTITIES = {
    "visualizing and understanding convolutional networks": "1311.2901",
    "deep inside convolutional networks visualising image classification models and saliency maps": "1312.6034",
    "a survey of methods for explaining black box models": "1802.01933",
    "grad cam visual explanations from deep networks via gradient based localization": "1610.02391",
}

_INVALID_MANUAL_IDENTITIES = {
    (
        "1810.03993",
        "benchmarking neural network interpretability",
    ),
}


def normalize_title(title: str) -> str:
    """生成仅用于精确去重的保守标题键。"""
    return " ".join(re.findall(r"[a-z0-9]+", title.casefold()))


def _repair_identity(record: dict) -> tuple[dict, bool]:
    result = dict(record)
    title_key = normalize_title(str(result.get("title", "")))
    canonical_id = _CLASSIC_IDENTITIES.get(title_key)
    if not canonical_id:
        return result, False

    changed = result.get("canonical_id") != canonical_id or result.get("arxiv_id") != canonical_id
    result["canonical_id"] = canonical_id
    result["arxiv_id"] = canonical_id
    result["version"] = max(1, int(result.get("version", 1) or 1))
    result["url"] = f"https://arxiv.org/abs/{canonical_id}"
    result["pdf_url"] = f"https://arxiv.org/pdf/{canonical_id}"
    return result, changed


def _repair_source(record: dict) -> dict:
    result = dict(record)
    source = str(result.get("source", "") or "").strip()
    url = str(result.get("url", "") or "")
    if not source:
        source = "arxiv" if "arxiv.org/" in url else "unknown"
    result["source"] = source

    sources: list[str] = []
    for item in [*(result.get("sources", []) or []), source]:
        if item and item not in sources:
            sources.append(item)
    result["sources"] = sources
    return result


def repair_records(records: list[dict]) -> tuple[list[dict], list[dict], dict[str, int]]:
    """修复索引并返回 ``(主索引, 隔离区, 报告)``，不丢弃原始记录。"""
    clean_by_title: OrderedDict[str, dict] = OrderedDict()
    quarantine: list[dict] = []
    report = {
        "input": len(records),
        "output": 0,
        "quarantined": 0,
        "duplicates_merged": 0,
        "identities_corrected": 0,
    }

    for original in records:
        record = dict(original)
        identity = (str(record.get("canonical_id", "")), normalize_title(record.get("title", "")))
        if record.get("quality_label") == "noise":
            record["quarantine_reason"] = "quality_label_noise"
            quarantine.append(record)
            continue
        if identity in _INVALID_MANUAL_IDENTITIES:
            record["quarantine_reason"] = "invalid_manual_identity"
            quarantine.append(record)
            continue

        record, corrected = _repair_identity(record)
        if corrected:
            report["identities_corrected"] += 1
        record = _repair_source(record)
        record = merge_paper_records({}, record)

        title_key = normalize_title(record.get("title", ""))
        dedupe_key = title_key or f"id:{record.get('canonical_id', '')}"
        if dedupe_key in clean_by_title:
            existing = clean_by_title[dedupe_key]
            record["canonical_id"] = existing["canonical_id"]
            record["arxiv_id"] = existing.get("arxiv_id", record.get("arxiv_id", ""))
            clean_by_title[dedupe_key] = merge_paper_records(existing, record)
            report["duplicates_merged"] += 1
        else:
            clean_by_title[dedupe_key] = record

    clean = list(clean_by_title.values())
    clean.sort(key=lambda item: (-int(item.get("year", 0) or 0), -float(item.get("relevance_score", 0) or 0)))
    report["output"] = len(clean)
    report["quarantined"] = len(quarantine)
    return clean, quarantine, report
