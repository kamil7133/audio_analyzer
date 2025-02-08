from spleeter.separator import Separator



class VocalSeparator:
    def __init__(self):
        self.separator = Separator('spleeter:2stems')

    def separate_vocals(self, audio_path, output_path):
        self.separator.separate_to_file(
            audio_path,
            output_path
        )