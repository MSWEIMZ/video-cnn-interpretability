import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from video_cnn_interp.dashboard import generate_dashboard_html


def test_dashboard_escapes_script_content_and_avoids_untrusted_inner_html():
    records = [
        {
            "title": "</script><img src=x onerror=alert(1)>",
            "year": 2026,
            "quality_label": "core",
            "relevance_score": 5.0,
            "url": "https://example.com",
            "topics": [],
        }
    ]
    html = generate_dashboard_html(records, {"total": 1, "by_label": {"core": 1}})
    assert "</script><img" not in html
    assert "innerHTML+=" not in html
    assert "textContent" in html
