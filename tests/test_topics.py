import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.topics import classify_paper_topics, cluster_papers_by_topic, get_topic_stats

def test_classify_3d_cnn_paper():
    rec = {"title": "R(2+1)D video classification interpretability", "abstract": "We study spatiotemporal convolution."}
    topics = classify_paper_topics(rec)
    assert "3d_cnn_explanation" in topics
    assert "action_recognition_interpretability" in topics

def test_classify_saliency_paper():
    rec = {"title": "Video saliency detection with Grad-CAM", "abstract": "We propose a saliency map method."}
    topics = classify_paper_topics(rec)
    assert "video_saliency" in topics

def test_cluster_returns_groups():
    records = [
        {"title": "R(2+1)D interpretability", "abstract": "3D CNN video", "quality_label": "core", "relevance_score": 5.0},
        {"title": "Video saliency", "abstract": "attention map detection", "quality_label": "strongly_related", "relevance_score": 3.0},
    ]
    clusters = cluster_papers_by_topic(records)
    assert len(clusters) >= 1

def test_topic_stats_sorted():
    records = [
        {"title": "R(2+1)D interpretability", "abstract": "3D CNN video", "quality_label": "core", "relevance_score": 5.0},
        {"title": "Video saliency with Grad-CAM", "abstract": "saliency map", "quality_label": "core", "relevance_score": 4.0},
    ]
    stats = get_topic_stats(records)
    assert len(stats) >= 1
    assert stats[0]["total"] >= stats[-1]["total"]
