"""Semantic Scholar 来源模块测试"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.sources.semantic_scholar import _normalize_paper


def test_normalize_ss_paper_basic():
    """测试 Semantic Scholar 论文格式转换（有 arXiv ID）"""
    raw = {
        "paperId": "abc123",
        "title": "Video Understanding with 3D CNN",
        "authors": [{"name": "Alice"}, {"name": "Bob"}],
        "abstract": "We study spatiotemporal convolution.",
        "year": 2024,
        "citationCount": 120,
        "venue": "CVPR",
        "externalIds": {"ArXiv": "2401.12345"},
        "url": "https://www.semanticscholar.org/paper/abc123",
        "fieldsOfStudy": ["Computer Science"],
    }
    result = _normalize_paper(raw)
    assert result["title"] == "Video Understanding with 3D CNN"
    assert result["authors"] == ["Alice", "Bob"]
    assert result["arxiv_id"] == "2401.12345"
    assert result["citation_count"] == 120
    assert result["venue"] == "CVPR"
    assert result["source"] == "semantic_scholar"


def test_normalize_ss_paper_no_arxiv():
    """测试没有 arXiv ID 的 Semantic Scholar 论文（paperId 作为 canonical_id）"""
    raw = {
        "paperId": "def456",
        "title": "A Survey of Video Methods",
        "authors": [{"name": "Charlie"}],
        "abstract": "A comprehensive review.",
        "year": 2023,
        "citationCount": 500,
        "venue": "IEEE TPAMI",
        "externalIds": {},
        "url": "https://www.semanticscholar.org/paper/def456",
    }
    result = _normalize_paper(raw)
    # 没有 arXiv ID 时，arxiv_id 会被设为 paperId（作为 canonical_id）
    assert result["arxiv_id"] == "def456"
    assert result["citation_count"] == 500
    assert result["venue"] == "IEEE TPAMI"
    assert result["source"] == "semantic_scholar"
