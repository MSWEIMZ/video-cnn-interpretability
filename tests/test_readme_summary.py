"""README 生成模块测试"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.readme import generate_main_readme


def test_readme_core_papers_have_summary():
    """核心论文表格应包含摘要列"""
    records = [
        {
            "title": "R(2+1)D Video Classification",
            "authors": ["Du Tran"],
            "year": 2018,
            "relevance_score": 7.5,
            "quality_label": "core",
            "url": "https://arxiv.org/abs/1711.11116",
            "source": "arxiv",
            "citation_count": 3500,
            "venue": "CVPR 2018",
            "summary_zh": "提出分解3D卷积为独立的空间和时间分量，在Kinetics上达到SOTA。",
        },
    ]
    stats = {"total": 1, "by_label": {"core": 1}}
    md = generate_main_readme(records, stats)
    # 应包含摘要内容
    assert "分解3D卷积" in md


def test_readme_core_papers_no_summary():
    """没有摘要的论文不应崩溃"""
    records = [
        {
            "title": "Some Paper",
            "authors": ["A"],
            "year": 2025,
            "relevance_score": 5.0,
            "quality_label": "core",
            "url": "#",
            "source": "arxiv",
            "citation_count": 0,
            "venue": "",
            "summary_zh": "",
        },
    ]
    stats = {"total": 1, "by_label": {"core": 1}}
    md = generate_main_readme(records, stats)
    assert "Some Paper" in md


def test_readme_year_fold_has_summary():
    """年份折叠视图应包含摘要列"""
    records = [
        {
            "title": "Grad-CAM for video",
            "authors": ["Selvaraju"],
            "year": 2017,
            "relevance_score": 5.5,
            "quality_label": "core",
            "url": "https://arxiv.org/abs/1610.02391",
            "source": "arxiv",
            "citation_count": 5324,
            "venue": "ICCV 2017",
            "summary_zh": "提出梯度加权类激活映射方法，实现CNN决策的可视化解释。",
        },
    ]
    stats = {"total": 1, "by_label": {"core": 1}}
    md = generate_main_readme(records, stats)
    # 年份折叠中应有摘要
    assert "梯度加权" in md
