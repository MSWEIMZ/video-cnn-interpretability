import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.storage import upsert_paper, get_all_records, get_stats

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
