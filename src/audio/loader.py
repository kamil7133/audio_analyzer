import librosa

class AudioLoader:
    def __init__(self, path):
        self.sample_rate = 22050
        self.path = path

    def load_audio(self):
        y, sr = librosa.load(self.path, sr=self.sample_rate)
        return y, sr
