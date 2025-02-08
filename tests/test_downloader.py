import pytest
from src.youtube.downloader import YoutubeDownloader
from unittest.mock import patch

@pytest.fixture
def downloader():
    return YoutubeDownloader()

@patch('yt_dlp.YoutubeDL.extract_info')
def test_download_audio(mock_extract_info, downloader):
    mock_extract_info.return_value = {'title': 'test_audio'}
    with patch('yt_dlp.YoutubeDL.download'):
        path = downloader.download_audio("https://youtube.com/watch?v=dQw4w9WgXcQ", "temp")
        assert path is not None
        assert "test_audio.wav" in path

@patch('yt_dlp.YoutubeDL.extract_info')
def test_get_video_info(mock_extract_info, downloader):
    mock_extract_info.return_value = {'title': 'test_audio', 'duration': 300}
    info = downloader.get_video_info("https://youtube.com/watch?v=dQw4w9WgXcQ")
    assert info == {'title': 'test_audio', 'duration': 300}