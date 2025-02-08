import pytest
import os
from src.optimization.cache import ResultsCache
from unittest.mock import patch

@pytest.fixture
def cache():
    return ResultsCache()

def test_cache_result(cache):
    cache.cache_result("dummy_path.wav", {"key": "C major", "bpm": 120})
    assert os.path.exists("cache/cache_metadata.json")

def test_get_cached_result(cache):
    cache.cache_result("dummy_path.wav", {"key": "C major", "bpm": 120})
    result = cache.get_cached_result("dummy_path.wav")
    assert result == {"key": "C major", "bpm": 120}

def test_clear_expired(cache):
    cache.cache_result("dummy_path.wav", {"key": "C major", "bpm": 120})
    cleared = cache.clear_expired()
    assert cleared == 0  # Cache nie wygasł jeszcze