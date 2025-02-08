import librosa
import numpy as np

class AudioAnalyzer:
    def detect_key(self, y, sr):
        return librosa.key_to_notes(librosa.key(y=y))

    def detect_tempo(self, y, sr):
        tempo = librosa.beat.tempo(y=y, sr=sr)
        return float(tempo[0])

    