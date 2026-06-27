"""飞书通知模块测试"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.notify import _build_daily_content, _build_no_new_content


def test_daily_content_with_papers():
    """有新增论文时，通知内容应包含统计、论文链接、引用量、作者"""
    new_records = [
        {
            "quality_label": "core",
            "title": "R(2+1)D Video Classification",
            "authors": ["Du Tran", "Heng Wang"],
            "url": "https://arxiv.org/abs/1711.11116",
            "relevance_score": 7.5,
            "citation_count": 3500,
            "venue": "CVPR 2018",
        },
        {
            "quality_label": "strongly_related",
            "title": "Network Dissection",
            "authors": ["David Bau", "Bolei Zhou"],
            "url": "https://arxiv.org/abs/1704.05796",
            "relevance_score": 4.0,
            "citation_count": 835,
            "venue": "CVPR 2017",
        },
    ]
    stats = {
        "total": 200,
        "by_label": {"core": 97, "strongly_related": 84, "weakly_related": 7},
        "noise_blocked_today": 3,
    }
    content = _build_daily_content(new_records, stats)
    # 应包含统计
    assert "200" in content
    assert "97" in content
    # 应包含论文标题
    assert "R(2+1)D" in content
    # 应包含链接
    assert "arxiv.org" in content
    # 应包含引用量
    assert "3500" in content
    # 应包含作者
    assert "Du Tran" in content
    # 应包含 venue
    assert "CVPR" in content
    # 应包含噪声拦截数
    assert "3" in content


def test_daily_content_no_new_papers():
    """无新增论文时，应返回简短的无新增内容"""
    stats = {
        "total": 200,
        "by_label": {"core": 97, "strongly_related": 84, "weakly_related": 7},
        "noise_blocked_today": 0,
    }
    content = _build_no_new_content(stats)
    assert "无新增" in content or "0" in content
    assert "200" in content  # 总数仍在


def test_daily_content_truncates_long_title():
    """超长标题应被截断"""
    new_records = [
        {
            "quality_label": "core",
            "title": "A" * 100,
            "authors": ["Author"],
            "url": "https://arxiv.org/abs/0000.00000",
            "relevance_score": 5.0,
            "citation_count": 0,
            "venue": "",
        },
    ]
    stats = {"total": 1, "by_label": {"core": 1}, "noise_blocked_today": 0}
    content = _build_daily_content(new_records, stats)
    # 标题应被截断到合理长度
    assert "A" * 80 not in content


def test_daily_content_no_url():
    """没有 URL 的论文不应崩溃"""
    new_records = [
        {
            "quality_label": "core",
            "title": "Some Paper",
            "authors": ["A"],
            "url": "",
            "relevance_score": 5.0,
            "citation_count": 0,
            "venue": "",
        },
    ]
    stats = {"total": 1, "by_label": {"core": 1}, "noise_blocked_today": 0}
    content = _build_daily_content(new_records, stats)
    assert "Some Paper" in content


def test_daily_content_limits_papers():
    """新增很多论文时，通知只显示前 5 篇核心 + 3 篇强相关"""
    new_records = []
    for i in range(10):
        new_records.append({
            "quality_label": "core",
            "title": f"Core Paper {i}",
            "authors": [f"Author{i}"],
            "url": f"https://arxiv.org/abs/0000.0000{i}",
            "relevance_score": 5.0,
            "citation_count": 0,
            "venue": "",
        })
    for i in range(5):
        new_records.append({
            "quality_label": "strongly_related",
            "title": f"Strong Paper {i}",
            "authors": [f"Author{i}"],
            "url": f"https://arxiv.org/abs/0000.1000{i}",
            "relevance_score": 3.0,
            "citation_count": 0,
            "venue": "",
        })
    stats = {"total": 100, "by_label": {"core": 50, "strongly_related": 40}, "noise_blocked_today": 0}
    content = _build_daily_content(new_records, stats)
    # 只显示 5 篇核心
    assert "Core Paper 0" in content
    assert "Core Paper 4" in content
    assert "Core Paper 9" not in content
    # 只显示 3 篇强相关
    assert "Strong Paper 0" in content
    assert "Strong Paper 2" in content
    assert "Strong Paper 4" not in content
