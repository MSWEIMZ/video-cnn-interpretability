import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from video_cnn_interp.normalizer import normalize_arxiv_id, extract_year_from_arxiv_id

def test_normalize_with_version():
    assert normalize_arxiv_id('2603.04976v2') == ('2603.04976', 2)

def test_normalize_without_version():
    assert normalize_arxiv_id('2603.04976') == ('2603.04976', 1)

def test_normalize_with_url_suffix():
    assert normalize_arxiv_id('2501.00001v1') == ('2501.00001', 1)

def test_normalize_empty():
    assert normalize_arxiv_id('') == ('unknown', 1)

def test_extract_year_standard():
    assert extract_year_from_arxiv_id('2603.04976') == 2026

def test_extract_year_2021():
    assert extract_year_from_arxiv_id('2109.09255') == 2021
