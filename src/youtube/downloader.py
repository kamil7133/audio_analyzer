from yt_dlp import YoutubeDL
import os
from typing import Optional


class YoutubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }

    def download_audio(self, url: str, output_dir: str) -> Optional[str]:
        try:
            self.ydl_opts['outtmpl'] = os.path.join(output_dir, '%(title)s.%(ext)s')

            with YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_title = info['title']

                ydl.download([url])

                output_path = os.path.join(output_dir, f"{video_title}.wav")
                return output_path if os.path.exists(output_path) else None

        except Exception as e:
            raise Exception(f"Error while downloading: {str(e)}")

    def get_video_info(self, url: str) -> dict:
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            raise Exception(f"Error while downloading information: {str(e)}")