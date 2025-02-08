import librosa
import numpy as np
from librosa.feature import spectral_centroid


class AudioAnalyzer:
    def __init__(self): # used krammer's profile
        self.major_profile = np.array([
            6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88
        ])

        self.minor_profile = np.array([
            6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17
        ])

    def detect_key(self, y, sr):
        '''
        Detects the key of the audio file using the chroma features and the major and minor profiles form krammer's profile

        :Args:
            y: audio signal
            sr: sample rate
        Returns:
            :str key of the audio file
        '''

        # Counting chroma features using CQT (constant Q transform)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)

        # Normalizing the chroma features
        chroma_normalized = np.mean(chroma, axis=1)
        chroma_normalized /= np.sum(chroma_normalized)

        # Keys
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        # Calculating correlation for every possible key
        key_correlation = []
        mode_correlation = []

        for i in range(12):
            rolled_chroma = np.roll(chroma_normalized, i)
            major_corr = np.corrcoef(rolled_chroma, self.major_profile)[0, 1]
            minor_corr = np.corrcoef(rolled_chroma, self.minor_profile)[0, 1]
            key_correlation.append(max(major_corr, minor_corr))
            mode_correlation.append((major_corr, minor_corr))

        # Find the key with the highest correlation
        best_shift = np.argmax(key_correlation)
        key_index = (12 - best_shift) % 12

        # Define mode (major or minor)
        major_corr, minor_corr = mode_correlation[best_shift]
        mode = "major" if major_corr > minor_corr else "minor"
        confidence = key_correlation[best_shift]

        # Additional energy analysis
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        mean_centroid = np.mean(spectral_centroids)

        # Harmonic analysis
        harmonics = librosa.effects.harmonic(y)
        harmonic_chromagram = librosa.feature.chroma_cqt(y=harmonics, sr=sr)

        if confidence < 0.5:
            harmonics = librosa.effects.harmonic(y)
            harmonic_chromagram = librosa.feature.chroma_cqt(y=harmonics, sr=sr)
            harmonic_correlation = np.corrcoef(
                np.mean(harmonic_chromagram, axis=1),
                self.major_profile if mode == "major" else self.minor_profile
            )[0, 1]

            if harmonic_correlation > 0.5:
                return f"{keys[key_index]} {mode} (uncertain)"

        return f"{keys[key_index]} {mode}"

    def detect_bpm(self, y: np.ndarray, sr: int) -> float:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
        tempo_harmonic = librosa.beat.tempo(
            y=librosa.effects.harmonic(y),
            sr=sr,
            aggregate=None
        )

        if np.abs(tempo[0] - np.median(tempo_harmonic)) > 10:
            tempo_dp = librosa.beat.tempo(
                y=y,
                sr=sr,
                aggregate=None,
                hop_length=512
            )

            return float(np.median([tempo[0], np.median(tempo_harmonic), np.median(tempo_dp)]))

        return float(tempo[0])

    def get_additional_info(self, y: np.ndarray, sr: int) -> dict:
        '''
        Get additional information about the audio file

        :param y: audio signal
        :param sr: sample rate
        :return:
            dict: additional information
        '''

        #onset envelope
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        #spectral centroid
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)

        return {
            'duration': librosa.get_duration(y=y, sr=sr),
            'tempo_confidence': self._get_tempo_confidence(y, sr),
            'key_strength': self._get_key_strength(y, sr),
            'spectral_bandwidth': np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)),
            'zero_crossing_rate': np.mean(librosa.feature.zero_crossing_rate(y))
        }


    def _get_tempo_confidence(self, y: np.ndarray, sr: int) -> float:
        '''
        Get the confidence of the tempo

        :param y: audio signal
        :param sr: sample rate
        :return:
            float: confidence of the tempo
        '''

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)

        return float(np.mean(pulse))

    def _get_key_strength(self, y: np.ndarray, sr: int) -> float:
        '''
        Get the strength of the key

        :param y: audio signal
        :param sr: sample rate
        :return:
            float: strength of the key
        '''

        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        return float(np.max(np.mean(chroma, axis=1)))


