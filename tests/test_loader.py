import pytest
import numpy as np
from src.audio.loader import AudioLoader
from unittest.mock import patch


@pytest.fixture
def loader():
    return AudioLoader()


@patch('librosa.load')
def test_load_audio(mock_load, loader):
    mock_load.return_value = (np.random.rand(22050 * 5), 22050)
    y, sr = loader.load_audio("dummy_path.wav")
    assert y is not None
    assert sr == 22050