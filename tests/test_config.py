import sys, pathlib, pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.config import load_app_config

def test_load_app_config_with_real_file():
    p = pathlib.Path(__file__).resolve().parents[1] / "search_config.json"
    cfg = load_app_config(str(p))
    assert len(cfg.core_queries) > 0
    assert len(cfg.expanded_queries) > 0
    assert len(cfg.exploratory_queries) > 0
    assert cfg.filters.years_from < cfg.filters.years_to
    assert cfg.scoring.min_relevance_score < cfg.scoring.core_threshold

def test_load_app_config_raises_on_missing_core(tmp_path):
    p = tmp_path / "search_config.json"
    p.write_text('{"queries": {}}', encoding="utf-8")
    with pytest.raises(ValueError, match="queries.core"):
        load_app_config(str(p))
