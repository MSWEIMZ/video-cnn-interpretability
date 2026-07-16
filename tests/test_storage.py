import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.storage import upsert_paper, get_all_records, get_stats, replace_index

def test_upsert_new_and_update(tmp_path):
    idx = tmp_path / "index.jsonl"
    rec1 = {
        "canonical_id": "2501.00001",
        "version": 1,
        "arxiv_id": "2501.00001v1",
        "title": "Test Paper",
        "authors": ["A"],
        "year": 2025,
        "published": "2025-01-01",
        "updated": "",
        "primary_category": "cs.CV",
        "categories": ["cs.CV"],
        "abstract": "Abstract",
        "url": "https://arxiv.org/abs/2501.00001v1",
        "pdf_url": "",
        "journal_ref": "",
        "search_category": "core",
        "search_query": "query",
        "query_type": "core",
        "relevance_score": 5.0,
        "quality_label": "core",
        "markdown_path": "",
    }
    assert upsert_paper(idx, rec1) is True
    assert upsert_paper(idx, rec1) is False
    records = get_all_records(idx)
    assert len(records) == 1
    stats = get_stats(idx)
    assert stats["total"] == 1


def test_upsert_preserves_enrichment_and_does_not_duplicate_history(tmp_path):
    idx = tmp_path / "index.jsonl"
    enriched = {
        "canonical_id": "2501.00001",
        "version": 1,
        "arxiv_id": "2501.00001v1",
        "title": "Test Paper",
        "authors": ["A"],
        "year": 2025,
        "published": "2025-01-01",
        "updated": "2025-01-02",
        "abstract": "Abstract",
        "url": "https://arxiv.org/abs/2501.00001v1",
        "citation_count": 42,
        "venue": "CVPR 2025",
        "summary_zh": "本文研究视频模型解释方法。",
        "topics": ["video_saliency"],
        "quality_label": "core",
        "relevance_score": 5.0,
        "source": "arxiv",
    }
    fresh_arxiv = {
        **enriched,
        "citation_count": 0,
        "venue": "",
        "summary_zh": "",
        "topics": [],
    }

    assert upsert_paper(idx, enriched) is True
    assert upsert_paper(idx, fresh_arxiv) is False
    assert upsert_paper(idx, fresh_arxiv) is False

    record = get_all_records(idx)[0]
    assert record["citation_count"] == 42
    assert record["venue"] == "CVPR 2025"
    assert record["summary_zh"] == "本文研究视频模型解释方法。"
    assert record["topics"] == ["video_saliency"]
    assert record.get("version_history", []) == []


def test_upsert_records_only_real_version_changes(tmp_path):
    idx = tmp_path / "index.jsonl"
    v1 = {
        "canonical_id": "2501.00001",
        "version": 1,
        "updated": "2025-01-01",
        "title": "Test Paper",
        "year": 2025,
    }
    v2 = {**v1, "version": 2, "updated": "2025-02-01"}

    upsert_paper(idx, v1)
    upsert_paper(idx, v2)
    upsert_paper(idx, v2)

    history = get_all_records(idx)[0]["version_history"]
    assert history == [{"version": 1, "updated": "2025-01-01"}]


def test_replace_index_removes_records_missing_from_repaired_dataset(tmp_path):
    idx = tmp_path / "index.jsonl"
    upsert_paper(idx, {"canonical_id": "a", "title": "A", "year": 2024})
    upsert_paper(idx, {"canonical_id": "b", "title": "B", "year": 2024})

    replace_index(idx, [{"canonical_id": "b", "title": "B", "year": 2024}])

    assert [record["canonical_id"] for record in get_all_records(idx)] == ["b"]
