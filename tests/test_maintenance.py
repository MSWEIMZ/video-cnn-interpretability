from video_cnn_interp.maintenance import repair_records


def _paper(canonical_id: str, title: str, **overrides) -> dict:
    record = {
        "canonical_id": canonical_id,
        "arxiv_id": canonical_id,
        "title": title,
        "url": f"https://arxiv.org/abs/{canonical_id}",
        "year": 2024,
        "version": 1,
        "updated": "2024-01-01",
        "version_history": [
            {"version": 1, "updated": "2024-01-01"},
            {"version": 1, "updated": "2024-01-01"},
        ],
        "quality_label": "core",
        "citation_count": 0,
        "source": "arxiv",
    }
    record.update(overrides)
    return record


def test_repair_records_merges_duplicate_titles_and_preserves_best_metadata():
    records = [
        _paper("1610.02391", "Grad-CAM: Visual Explanations", citation_count=100),
        _paper(
            "wrong-id",
            "Grad-CAM: Visual Explanations",
            citation_count=20,
            summary_zh="这是一篇中文导读",
            source="manual",
        ),
    ]

    clean, quarantine, report = repair_records(records)

    assert len(clean) == 1
    assert quarantine == []
    assert clean[0]["canonical_id"] == "1610.02391"
    assert clean[0]["citation_count"] == 100
    assert clean[0]["summary_zh"] == "这是一篇中文导读"
    assert set(clean[0]["sources"]) == {"arxiv", "manual"}
    assert report["duplicates_merged"] == 1


def test_repair_records_quarantines_noise_and_known_invalid_manual_record():
    records = [
        _paper("noise", "Unrelated Paper", quality_label="noise"),
        _paper(
            "1810.03993",
            "Benchmarking Neural Network Interpretability",
            source="manual",
        ),
    ]

    clean, quarantine, report = repair_records(records)

    assert clean == []
    assert {record["quarantine_reason"] for record in quarantine} == {
        "quality_label_noise",
        "invalid_manual_identity",
    }
    assert report["quarantined"] == 2


def test_repair_records_corrects_known_classic_paper_identities():
    records = [
        _paper(
            "1312.6034",
            "Visualizing and Understanding Convolutional Networks",
            source="manual",
        ),
        _paper(
            "1412.0767",
            "Deep Inside Convolutional Networks: Visualising Image Classification Models and Saliency Maps",
            source="manual",
        ),
        _paper(
            "1506.01497",
            "A survey of methods for explaining Black Box Models",
            source="manual",
        ),
    ]

    clean, _, report = repair_records(records)

    by_title = {record["title"].lower(): record for record in clean}
    assert by_title["visualizing and understanding convolutional networks"]["canonical_id"] == "1311.2901"
    assert by_title[
        "deep inside convolutional networks: visualising image classification models and saliency maps"
    ]["canonical_id"] == "1312.6034"
    assert by_title["a survey of methods for explaining black box models"]["canonical_id"] == "1802.01933"
    assert all(record["url"].endswith(record["canonical_id"]) for record in clean)
    assert report["identities_corrected"] == 3


def test_repair_records_compacts_history_and_infers_missing_source():
    record = _paper("2401.00001", "A Paper", source="")

    clean, _, _ = repair_records([record])

    assert clean[0]["source"] == "arxiv"
    assert clean[0]["sources"] == ["arxiv"]
    assert clean[0]["version_history"] == [
        {"version": 1, "updated": "2024-01-01"}
    ]
