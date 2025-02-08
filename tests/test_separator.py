import pytest
from src.audio.separator import VocalSeparator
from unittest.mock import patch


@pytest.fixture
def separator():
    return VocalSeparator()


@patch('spleeter.separator.Separator.separate_to_file')
def test_separate_vocals(mock_separate, separator):
    separator.separate_vocals("dummy_path.wav", "output_dir")
    mock_separate.assert_called_once_with("dummy_path.wav", "output_dir")