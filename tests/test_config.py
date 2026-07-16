import sys, pathlib, pytest, json
from datetime import datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.config import load_app_config

def test_load_app_config_with_real_file():
    p = pathlib.Path(__file__).resolve().parents[1] / "search_config.json"
    cfg = load_app_config(str(p))
    assert len(cfg.core_queries) > 0
    assert len(cfg.expanded_queries) > 0
    assert len(cfg.exploratory_queries) > 0
    assert cfg.filters.years_from < cfg.filters.years_to
    assert "video" in cfg.filters.required_domain_keywords
    assert cfg.scoring.min_relevance_score < cfg.scoring.core_threshold

def test_load_app_config_raises_on_missing_core(tmp_path):
    p = tmp_path / "search_config.json"
    p.write_text('{"queries": {}}', encoding="utf-8")
    with pytest.raises(ValueError, match="queries.core"):
        load_app_config(str(p))


def test_years_to_current_is_resolved(tmp_path):
    p = tmp_path / "search_config.json"
    p.write_text(
        json.dumps({"queries": {"core": ["video"]}, "filters": {"years_to": "current"}}),
        encoding="utf-8",
    )
    assert load_app_config(p).filters.years_to == datetime.now().year


def test_invalid_threshold_order_is_rejected(tmp_path):
    p = tmp_path / "search_config.json"
    p.write_text(
        json.dumps(
            {
                "queries": {"core": ["video"]},
                "scoring": {
                    "min_relevance_score": 4.0,
                    "strongly_related_threshold": 3.0,
                    "core_threshold": 2.0,
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="评分阈值"):
        load_app_config(p)
