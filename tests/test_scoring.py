import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.config import load_app_config
from video_cnn_interp.scorer import compute_relevance_score, assign_quality_label, is_video_domain_relevant

def _cfg():
    p = pathlib.Path(__file__).resolve().parents[1] / "search_config.json"
    return load_app_config(str(p))

def test_core_paper_scores_high():
    cfg = _cfg()
    paper = {
        'title': 'R(2+1)D Video Classification Interpretability',
        'summary': 'We study spatiotemporal convolution for video action recognition and explainability of 3D CNN.',
        'categories': ['cs.CV'],
    }
    score = compute_relevance_score(paper, 'core', cfg)
    assert score >= cfg.scoring.core_threshold
    assert assign_quality_label(score, cfg) == 'core'

def test_noise_paper_scores_low():
    cfg = _cfg()
    paper = {
        'title': 'Search for gravitational waves from LHCb collider',
        'summary': 'We present particle physics results from cosmology observations.',
        'categories': ['hep-ex'],
    }
    score = compute_relevance_score(paper, 'exploratory', cfg)
    assert score < cfg.scoring.min_relevance_score
    assert assign_quality_label(score, cfg) == 'noise'

def test_weakly_related_paper():
    cfg = _cfg()
    paper = {
        'title': 'Video attention mechanism visualization in deep neural networks',
        'summary': 'We propose a method for video attention visualization using saliency maps.',
        'categories': ['cs.CV'],
    }
    score = compute_relevance_score(paper, 'expanded', cfg)
    label = assign_quality_label(score, cfg)
    assert label in ('weakly_related', 'strongly_related', 'core')


def test_video_domain_gate_rejects_generic_xai_and_sensor_papers():
    cfg = _cfg()
    generic_xai = {
        "title": "Applied Explainability for Large Language Models",
        "abstract": "We compare SHAP and LIME for text generation systems.",
    }
    sensor = {
        "title": "Condition Diagnosis for Ball Bearings",
        "abstract": "A convolutional network analyzes ultrasonic sensor signals.",
    }

    assert not is_video_domain_relevant(generic_xai, cfg.filters.required_domain_keywords)
    assert not is_video_domain_relevant(sensor, cfg.filters.required_domain_keywords)


def test_video_domain_gate_accepts_video_and_spatiotemporal_work():
    cfg = _cfg()
    paper = {
        "title": "Interpretable Spatiotemporal Models for Action Recognition",
        "abstract": "We explain a 3D CNN trained on action clips.",
    }

    assert is_video_domain_relevant(paper, cfg.filters.required_domain_keywords)
