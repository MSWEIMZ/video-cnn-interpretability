import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.config import load_app_config
from video_cnn_interp.scorer import compute_relevance_score, assign_quality_label

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
