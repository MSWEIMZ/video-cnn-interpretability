import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.readme import generate_all_papers, generate_main_readme

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
    assert "ALL_PAPERS_zh.md" in md
    assert "Core Paper" in md


def test_chinese_readme_uses_chinese_navigation_targets():
    records = [
        {
            "title": "Core Paper",
            "authors": ["A"],
            "year": 2026,
            "relevance_score": 5.0,
            "quality_label": "core",
            "url": "#",
            "source": "arxiv",
            "summary_zh": "本文研究视频理解。",
        }
    ]
    stats = {"total": 1, "by_label": {"core": 1}}
    md = generate_main_readme(records, stats, lang="zh")
    assert "快速导航" in md
    assert "ALL_PAPERS_zh.md" in md
    assert "#-高影响力论文-top-5" in md
    assert "TOPICS.md" in md
    assert "TRENDS.md" in md
    assert "dashboard.html" in md


def test_influential_section_only_uses_core_papers():
    records = [
        {
            "title": "Relevant Core",
            "authors": ["A"],
            "year": 2020,
            "citation_count": 10,
            "relevance_score": 5.0,
            "quality_label": "core",
            "url": "#",
        },
        {
            "title": "Highly Cited But Secondary",
            "authors": ["B"],
            "year": 2020,
            "citation_count": 100000,
            "relevance_score": 3.0,
            "quality_label": "strongly_related",
            "url": "#",
        },
    ]
    stats = {"total": 2, "by_label": {"core": 1, "strongly_related": 1}}

    md = generate_main_readme(records, stats, lang="en")
    influential = md.split("## 🏆 Top 5 Most Influential", 1)[1].split("## 🔥 Latest Trending", 1)[0]

    assert "Relevant Core" in influential
    assert "Highly Cited But Secondary" not in influential


def test_markdown_table_cells_are_escaped():
    records = [
        {
            "title": "Video | XAI\nStudy",
            "authors": ["A | B"],
            "year": 2026,
            "relevance_score": 5.0,
            "quality_label": "core",
            "url": "https://example.com/paper",
            "summary_zh": "方法 | 结果\n清晰",
        }
    ]

    md = generate_all_papers(records, lang="zh")

    assert "Video \\| XAI Study" in md
    assert "A \\| B" in md
    assert "方法 \\| 结果 清晰" in md
