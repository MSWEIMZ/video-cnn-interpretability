import json
from types import SimpleNamespace

import video_cnn_interp.cli as cli


def test_run_repair_rebuilds_clean_index_and_preserves_quarantine(tmp_path, monkeypatch):
    papers = tmp_path / "papers"
    papers.mkdir()
    records = [
        {
            "canonical_id": "2401.00001",
            "arxiv_id": "2401.00001",
            "title": "Interpreting Video Models with Temporal Saliency",
            "abstract": "We explain temporal predictions with saliency maps.",
            "year": 2024,
            "version": 1,
            "url": "https://arxiv.org/abs/2401.00001",
            "quality_label": "core",
            "relevance_score": 5.0,
            "query_type": "core",
            "source": "arxiv",
        },
        {
            "canonical_id": "noise",
            "title": "Unrelated",
            "year": 2024,
            "quality_label": "noise",
        },
        {
            "canonical_id": "off-topic",
            "title": "Applied Explainability for Large Language Models",
            "abstract": "We explain text generation models.",
            "year": 2024,
            "quality_label": "strongly_related",
            "source": "arxiv",
        },
    ]
    (papers / "index.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    (papers / "quarantine.jsonl").write_text(
        json.dumps(
            {
                "canonical_id": "previously-quarantined",
                "title": "Previously Quarantined",
                "quarantine_reason": "manual_review",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = SimpleNamespace(
        runtime=SimpleNamespace(output_dir="papers"),
        filters=SimpleNamespace(required_domain_keywords=["video", "spatiotemporal", "action recognition"]),
    )
    monkeypatch.setattr(cli, "load_app_config", lambda _: config)

    report = cli.run_repair(tmp_path)

    clean = [json.loads(line) for line in (papers / "index.jsonl").read_text(encoding="utf-8").splitlines()]
    quarantine = [
        json.loads(line)
        for line in (papers / "quarantine.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(clean) == 1
    assert any("\u4e00" <= char <= "\u9fff" for char in clean[0]["summary_zh"])
    assert {record["quarantine_reason"] for record in quarantine} == {
        "quality_label_noise",
        "outside_video_domain",
        "manual_review",
    }
    assert report["quarantined"] == 3
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "README_zh.md").exists()
