import os
import hashlib
import pickle
import json
import time
from typing import Optional, Dict, Any


class ResultsCache:
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the cache system.

        Args:
            cache_dir (str): Directory to store cache files
        """
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(cache_dir, "cache_metadata.json")
        self._ensure_cache_dir()
        self.cache_ttl = 7 * 24 * 60 * 60  # 7 days in seconds

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        os.makedirs(self.cache_dir, exist_ok=True)
        if not os.path.exists(self.metadata_file):
            self._save_metadata({})

    def _get_file_hash(self, file_path: str) -> str:
        """
        Generate MD5 hash of file content and modification time.

        Args:
            file_path (str): Path to the audio file

        Returns:
            str: Hash string
        """
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)  # Read in 64kb chunks
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)

        # Include file modification time in hash
        mod_time = str(os.path.getmtime(file_path))
        hasher.update(mod_time.encode())

        return hasher.hexdigest()

    def _get_cache_path(self, cache_key: str) -> str:
        """Get the full path for a cache file."""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")

    def _load_metadata(self) -> Dict:
        """Load cache metadata from JSON file."""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_metadata(self, metadata: Dict) -> None:
        """Save cache metadata to JSON file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f)

    def get_cached_result(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis results for an audio file.

        Args:
            audio_path (str): Path to the audio file

        Returns:
            Optional[Dict[str, Any]]: Cached results or None if not found/expired
        """
        if not os.path.exists(audio_path):
            return None

        cache_key = self._get_file_hash(audio_path)
        cache_path = self._get_cache_path(cache_key)
        metadata = self._load_metadata()

        # Check if cache exists and is valid
        if cache_key in metadata:
            cache_time = metadata[cache_key]['timestamp']
            if time.time() - cache_time <= self.cache_ttl:
                try:
                    with open(cache_path, 'rb') as f:
                        return pickle.load(f)
                except (FileNotFoundError, pickle.UnpicklingError):
                    pass

        return None

    def cache_result(self, audio_path: str, result: Dict[str, Any]) -> None:
        """
        Cache analysis results for an audio file.

        Args:
            audio_path (str): Path to the audio file
            result (Dict[str, Any]): Analysis results to cache
        """
        cache_key = self._get_file_hash(audio_path)
        cache_path = self._get_cache_path(cache_key)

        # Save results
        with open(cache_path, 'wb') as f:
            pickle.dump(result, f)

        # Update metadata
        metadata = self._load_metadata()
        metadata[cache_key] = {
            'timestamp': time.time(),
            'file_path': audio_path
        }
        self._save_metadata(metadata)

    def clear_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            int: Number of entries cleared
        """
        metadata = self._load_metadata()
        current_time = time.time()
        expired_keys = []

        for key, data in metadata.items():
            if current_time - data['timestamp'] > self.cache_ttl:
                cache_path = self._get_cache_path(key)
                try:
                    os.remove(cache_path)
                except FileNotFoundError:
                    pass
                expired_keys.append(key)

        for key in expired_keys:
            del metadata[key]

        self._save_metadata(metadata)
        return len(expired_keys)

    def clear_all(self) -> None:
        """Clear all cache entries."""
        metadata = self._load_metadata()

        for key in metadata:
            cache_path = self._get_cache_path(key)
            try:
                os.remove(cache_path)
            except FileNotFoundError:
                pass

        self._save_metadata({})