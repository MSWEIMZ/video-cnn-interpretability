import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.readme import generate_main_readme

def test_readme_contains_sections():
    records = [
        {"title": "Core Paper", "authors": ["A"], "year": 2026, "relevance_score": 5.0, "quality_label": "core", "url": "#"},
        {"title": "Strong Paper", "authors": ["B"], "year": 2025, "relevance_score": 3.0, "quality_label": "strongly_related", "url": "#"},
        {"title": "Weak Paper", "authors": ["C"], "year": 2024, "relevance_score": 2.0, "quality_label": "weakly_related", "url": "#"},
    ]
    stats = {"total": 3, "by_label": {"core": 1, "strongly_related": 1, "weakly_related": 1}}
    md = generate_main_readme(records, stats)
    assert "统计概览" in md
    assert "最新核心论文" in md
    assert "ALL_PAPERS.md" in md
    assert "Core Paper" in md
