"""回填功能集成测试"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.summarizer import enhance_record
from video_cnn_interp.topics import classify_paper_topics


def test_enhance_record_adds_all_fields():
    rec = {
        "title": "R(2+1)D Video Classification Interpretability",
        "abstract": "We study spatiotemporal convolution for video action recognition. Our method uses Grad-CAM for visualization.",
        "quality_label": "core",
    }
    result = enhance_record(rec)
    assert "summary_zh" in result
    assert "method_type" in result
    assert "relation_to_r2plus1d" in result
    assert "mentions_r2plus1d" in result
    assert "r2plus1d_context" in result
    assert "one_line_summary" in result
    assert len(result["summary_zh"]) > 0

def test_enhance_detects_gradient_method():
    rec = {
        "title": "Grad-CAM for video understanding",
        "abstract": "We propose gradient-based visualization.",
        "quality_label": "core",
    }
    result = enhance_record(rec)
    assert "gradient-based" in result["method_type"]

def test_enhance_detects_r2plus1d():
    rec = {
        "title": "R(2+1)D spatiotemporal convolution",
        "abstract": "We decompose 3D convolutions using factored convolution approach.",
        "quality_label": "core",
    }
    result = enhance_record(rec)
    assert result["mentions_r2plus1d"] is True
    assert len(result["r2plus1d_context"]) > 0

def test_topics_classify_after_enhance():
    rec = {
        "title": "R(2+1)D video classification interpretability",
        "abstract": "We study spatiotemporal convolution for video action recognition.",
        "quality_label": "core",
    }
    rec = enhance_record(rec)
    topics = classify_paper_topics(rec)
    assert len(topics) > 0
    assert "3d_cnn_explanation" in topics or "action_recognition_interpretability" in topics

def test_enhance_empty_abstract():
    rec = {
        "title": "Some Paper",
        "abstract": "",
        "quality_label": "weakly_related",
    }
    result = enhance_record(rec)
    assert result["summary_zh"] != ""
    assert result["method_type"] == "other"
