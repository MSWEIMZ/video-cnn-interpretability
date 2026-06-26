"""多源去重测试"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.collector import _is_duplicate, _deduplicate


def test_same_arxiv_id_is_duplicate():
    a = {"arxiv_id": "2401.12345", "title": "Paper A"}
    b = {"arxiv_id": "2401.12345", "title": "Paper B"}
    assert _is_duplicate(a, b) is True

def test_similar_title_is_duplicate():
    a = {"arxiv_id": "", "title": "Video Understanding with Deep Neural Networks"}
    b = {"arxiv_id": "", "title": "Video Understanding with Deep Neural Network"}
    assert _is_duplicate(a, b) is True

def test_different_papers_not_duplicate():
    a = {"arxiv_id": "2401.12345", "title": "Video Classification with 3D Convolutional Neural Networks"}
    b = {"arxiv_id": "2401.99999", "title": "Object Detection in Autonomous Driving Scenarios"}
    assert _is_duplicate(a, b) is False

def test_deduplicate_removes_same_arxiv_id():
    papers = [
        {"arxiv_id": "2401.00001", "title": "Video Classification with 3D CNN"},
        {"arxiv_id": "2401.00001", "title": "Video Classification with 3D CNN duplicate"},
        {"arxiv_id": "2401.00002", "title": "Object Detection in Driving Scenarios"},
    ]
    seen = set()
    result = _deduplicate(papers, seen)
    assert len(result) == 2
    assert result[0]["arxiv_id"] == "2401.00001"
    assert result[1]["arxiv_id"] == "2401.00002"

def test_deduplicate_respects_seen_ids():
    papers = [
        {"arxiv_id": "2401.00001", "title": "Video Classification with 3D CNN"},
        {"arxiv_id": "2401.00002", "title": "Object Detection in Driving Scenarios"},
    ]
    seen = {"2401.00001"}
    result = _deduplicate(papers, seen)
    assert len(result) == 1
    assert result[0]["arxiv_id"] == "2401.00002"
