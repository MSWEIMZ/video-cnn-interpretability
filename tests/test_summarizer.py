"""摘要增强模块测试"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.summarizer import generate_summary_zh, enhance_record


def test_summary_zh_with_abstract():
    """有摘要时应返回精炼的一句话（≤80字）"""
    rec = {
        "title": "R(2+1)D Video Classification",
        "abstract": "We propose a novel spatiotemporal convolutional architecture that decomposes 3D convolutions into spatial and temporal components. Our method achieves state-of-the-art results on Kinetics and Sports-1M benchmarks.",
    }
    summary = generate_summary_zh(rec)
    assert len(summary) > 0
    assert len(summary) <= 80
    # 应包含核心信息
    assert "R(2+1)D" in summary or "spatiotemporal" in summary.lower() or "convolution" in summary.lower()


def test_summary_zh_no_abstract():
    """无摘要时应返回截断的标题"""
    rec = {"title": "A Very Long Paper Title About Video Understanding", "abstract": ""}
    summary = generate_summary_zh(rec)
    assert len(summary) > 0
    assert len(summary) <= 80


def test_summary_zh_truncates():
    """超长摘要应被截断到 80 字以内"""
    rec = {
        "title": "Test",
        "abstract": "This is a very long abstract. " * 20 + "It covers many topics including video understanding, action recognition, temporal modeling, and more.",
    }
    summary = generate_summary_zh(rec)
    assert len(summary) <= 80


def test_summary_zh_in_enhance_record():
    """enhance_record 应设置 summary_zh 字段"""
    rec = {
        "title": "Grad-CAM for video",
        "abstract": "We propose Gradient-weighted Class Activation Mapping for visual explanations of deep networks.",
        "quality_label": "core",
    }
    result = enhance_record(rec)
    assert "summary_zh" in result
    assert len(result["summary_zh"]) > 0
