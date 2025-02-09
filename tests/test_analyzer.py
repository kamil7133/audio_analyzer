import pytest
import numpy as np
from src.audio.analyzer import AudioAnalyzer


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
    assert 60 <= bpm <= 180