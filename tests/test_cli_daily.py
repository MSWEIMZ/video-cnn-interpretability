import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from video_cnn_interp import cli
from video_cnn_interp.storage import get_all_records, upsert_paper


def _raw(arxiv_id: str, title: str) -> dict:
    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": ["A"],
        "summary": "We study video understanding with temporal attention.",
        "published": "2026-07-01",
        "updated": "2026-07-01",
        "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        "categories": ["cs.CV"],
        "primary_category": "cs.CV",
        "citation_count": 0,
        "venue": "",
        "source": "arxiv",
    }


def test_run_daily_notifies_only_truly_new_records(tmp_path, monkeypatch):
    config = json.loads(
        (pathlib.Path(__file__).resolve().parents[1] / "search_config.json").read_text(encoding="utf-8")
    )
    config["runtime"]["notify_feishu"] = True
    config["runtime"]["crossref_enabled"] = False
    (tmp_path / "search_config.json").write_text(json.dumps(config), encoding="utf-8")

    index_path = tmp_path / "papers" / "index.jsonl"
    existing = {
        "canonical_id": "2607.00001",
        "version": 1,
        "arxiv_id": "2607.00001v1",
        "title": "Existing Video Paper",
        "authors": ["A"],
        "year": 2026,
        "published": "2026-07-01",
        "updated": "2026-07-01",
        "abstract": "Existing abstract",
        "url": "https://arxiv.org/abs/2607.00001v1",
        "citation_count": 99,
        "venue": "CVPR 2026",
        "summary_zh": "本文研究已有视频模型。",
        "quality_label": "core",
        "relevance_score": 5.0,
        "source": "arxiv",
    }
    upsert_paper(index_path, existing)

    candidates = [
        ("core", "video understanding", _raw("2607.00001v1", "Existing Video Paper")),
        ("core", "video understanding", _raw("2607.00002v1", "New Video Paper")),
    ]
    sent = []
    monkeypatch.setattr(cli, "collect_candidates", lambda _config: candidates)
    monkeypatch.setattr(cli, "send_daily_digest", lambda records, stats, errors=None: sent.append(records) or True)

    cli.run_daily(tmp_path)

    assert len(sent) == 1
    assert [record["title"] for record in sent[0]] == ["New Video Paper"]
    records = {record["canonical_id"]: record for record in get_all_records(index_path)}
    assert records["2607.00001"]["citation_count"] == 99
    assert records["2607.00001"]["venue"] == "CVPR 2026"
    assert records["2607.00001"].get("version_history", []) == []
    assert any("\u4e00" <= ch <= "\u9fff" for ch in records["2607.00002"]["summary_zh"])
