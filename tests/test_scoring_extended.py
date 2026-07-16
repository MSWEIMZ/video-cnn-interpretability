"""评分模块补充测试 - venue/citation/survey 边界 case"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.config import load_app_config
from video_cnn_interp.scorer import (
    compute_relevance_score, assign_quality_label,
    _detect_venue_bonus, _detect_survey_bonus, _apply_citation_bonus,
)

def _cfg():
    p = pathlib.Path(__file__).resolve().parents[1] / "search_config.json"
    return load_app_config(str(p))


def test_venue_bonus_cvpr():
    assert _detect_venue_bonus("CVPR 2024") == 0.5
    assert _detect_venue_bonus("Accepted at CVPR 2024") == 0.5

def test_venue_bonus_neurips():
    assert _detect_venue_bonus("NeurIPS 2023") == 0.4

def test_venue_bonus_none():
    assert _detect_venue_bonus("Some Random Journal") == 0.0
    assert _detect_venue_bonus("") == 0.0

def test_venue_bonus_case_insensitive():
    assert _detect_venue_bonus("cvpr 2024") == 0.5
    assert _detect_venue_bonus("CVPR") == 0.5

def test_survey_bonus_positive():
    assert _detect_survey_bonus("A comprehensive survey of video methods") == 0.8
    assert _detect_survey_bonus("We present a benchmark dataset") == 0.8
    assert _detect_survey_bonus("Taxonomy of deep learning approaches") == 0.8

def test_survey_bonus_negative():
    assert _detect_survey_bonus("Video classification with 3D CNN") == 0.0
    assert _detect_survey_bonus("") == 0.0

def test_citation_bonus_above_threshold():
    assert _apply_citation_bonus(100, 50, 0.5) == 0.5
    assert _apply_citation_bonus(50, 50, 0.5) == 0.5
    assert _apply_citation_bonus(999, 50, 0.5) == 0.5

def test_citation_bonus_below_threshold():
    assert _apply_citation_bonus(0, 50, 0.5) == 0.0
    assert _apply_citation_bonus(49, 50, 0.5) == 0.0
    assert _apply_citation_bonus(10, 50, 0.5) == 0.0

def test_cvpr_paper_scores_higher():
    cfg = _cfg()
    base_paper = {
        'title': 'Video action recognition with attention',
        'summary': 'We study video temporal modeling.',
        'categories': ['cs.CV'],
        'citation_count': 0,
        'venue': '',
    }
    cvpr_paper = dict(base_paper)
    cvpr_paper['venue'] = 'CVPR 2024'
    s_base = compute_relevance_score(base_paper, 'core', cfg)
    s_cvpr = compute_relevance_score(cvpr_paper, 'core', cfg)
    assert s_cvpr > s_base

def test_high_citation_paper_scores_higher():
    cfg = _cfg()
    base_paper = {
        'title': 'Video action recognition with attention',
        'summary': 'We study video temporal modeling.',
        'categories': ['cs.CV'],
        'citation_count': 0,
        'venue': '',
    }
    cited_paper = dict(base_paper)
    cited_paper['citation_count'] = 200
    s_base = compute_relevance_score(base_paper, 'core', cfg)
    s_cited = compute_relevance_score(cited_paper, 'core', cfg)
    assert s_cited > s_base

def test_survey_paper_not_noise():
    cfg = _cfg()
    paper = {
        'title': 'A survey of video understanding',
        'summary': 'We provide a comprehensive review.',
        'categories': ['cs.CV'],
        'citation_count': 0,
        'venue': '',
    }
    score = compute_relevance_score(paper, 'exploratory', cfg)
    assert score >= cfg.scoring.min_relevance_score


def test_scoring_uses_configured_bonus_values():
    cfg = _cfg()
    cfg.scoring.citation_bonus_threshold = 1
    cfg.scoring.citation_bonus = 2.0
    cfg.scoring.survey_bonus = 1.7
    cfg.scoring.venue_bonus = {"CVPR": 1.3}
    paper = {
        "title": "A survey of video understanding",
        "summary": "A review of temporal models.",
        "categories": [],
        "citation_count": 1,
        "venue": "CVPR 2026",
    }

    score = compute_relevance_score(paper, "exploratory", cfg)
    baseline = cfg.scoring.keyword_weights["exploratory"]
    topic_hits = 2 * cfg.scoring.topic_bonus_per_hit
    title_bonus = cfg.scoring.video_in_title_bonus
    assert score == round(baseline + topic_hits + title_bonus + 2.0 + 1.7 + 1.3, 2)
