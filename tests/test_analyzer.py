import pytest
import numpy as np
from src.audio.analyzer import AudioAnalyzer
from unittest.mock import patch

@pytest.fixture
def analyzer():
    return AudioAnalyzer()

def test_detect_key(analyzer):
    y = np.random.rand(22050 * 5)  # 5 sekund audio
    sr = 22050
    key = analyzer.detect_key(y, sr)
    assert isinstance(key, str)
    assert "major" in key or "minor" in key

def test_detect_bpm(analyzer):
    y = np.random.rand(22050 * 5)  # 5 sekund audio
    sr = 22050
    bpm = analyzer.detect_bpm(y, sr)
    assert isinstance(bpm, int)
    assert 60 <= bpm <= 180  # Zakładamy, że BPM będzie w rozsądnym zakresie

def test_get_additional_info(analyzer):
    y = np.random.rand(22050 * 5)  # 5 sekund audio
    sr = 22050
    info = analyzer.get_additional_info(y, sr)
    assert isinstance(info, dict)
    assert 'duration' in info
    assert 'tempo_confidence' in info
    assert 'key_strength' in info