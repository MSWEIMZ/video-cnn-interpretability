import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from video_cnn_interp.sources.crossref import select_best_match, title_similarity


def test_title_similarity_is_case_and_punctuation_insensitive():
    assert title_similarity("Grad-CAM: Visual Explanations", "grad cam visual explanations") > 0.95


def test_select_best_match_rejects_wrong_title_or_year():
    record = {"title": "Video Understanding with 3D CNN", "year": 2025}
    items = [
        {
            "title": ["Unrelated Medical Study"],
            "published": {"date-parts": [[2025]]},
        },
        {
            "title": ["Video Understanding with 3D CNN"],
            "published": {"date-parts": [[2018]]},
        },
    ]
    assert select_best_match(record, items) is None


def test_select_best_match_accepts_high_confidence_candidate():
    record = {"title": "Video Understanding with 3D CNN", "year": 2025}
    item = {
        "title": ["Video Understanding with 3D CNN"],
        "published": {"date-parts": [[2024]]},
    }
    assert select_best_match(record, [item]) == item
