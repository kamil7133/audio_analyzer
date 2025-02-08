import librosa

class AudioLoader:
    def __init__(self):
        self.sample_rate = 22050

    def load_audio(self, file_path):
        y, sr = librosa.load(file_path, sr=self.sample_rate)
        return y, sr
