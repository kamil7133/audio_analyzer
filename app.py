import streamlit as st
import os
import hashlib
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from filelock import FileLock
from src.audio.analyzer import AudioAnalyzer
from src.audio.loader import AudioLoader
from src.audio.separator import VocalSeparator
from src.optimization.cache import ResultsCache
from src.youtube.downloader import YoutubeDownloader

# Configuration
st.set_page_config(page_title="Audio Analyzer Pro", layout="wide")
MAX_FILE_SIZE = 300  # MB


def create_temp_dir():
    """Create temporary directories with proper permissions"""
    temp_dirs = [
        Path("temp/uploads"),
        Path("temp/separated")
    ]

    for dir_path in temp_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(dir_path, 0o755)
        except Exception:
            pass


def safe_write(path, data):
    """Atomic file write with locking"""
    path = Path(path)
    lock_path = path.with_suffix(path.suffix + '.lock')

    try:
        with FileLock(str(lock_path)):
            with path.open("wb") as f:
                f.write(data)
    finally:
        if lock_path.exists():
            lock_path.unlink()


def read_file_chunked(path):
    """Memory-efficient file reading with locking"""
    path = Path(path)
    lock_path = path.with_suffix(path.suffix + '.lock')

    with FileLock(str(lock_path)):
        with path.open("rb") as f:
            while chunk := f.read(8192 * 1024):  # 8MB chunks
                yield chunk


@st.cache_data(show_spinner=False)
def process_audio(file_path, _separator, _cache):
    """Process audio with enhanced error handling"""
    try:
        file_path = Path(file_path)
        process_id = uuid.uuid4().hex
        output_dir = Path("temp/separated") / process_id
        output_dir.mkdir(exist_ok=True)

        # Generate safe output paths
        vocal_path = output_dir / "vocals.wav"
        backing_path = output_dir / "accompaniment.wav"

        # Parallel execution with error propagation
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_sep = executor.submit(
                _separator.separate_vocals,
                str(file_path),
                str(output_dir)
            )
            future_analysis = executor.submit(
                analyze_audio,
                str(file_path),
                _cache
            )

            # Get results with timeout
            separation_result = future_sep.result(timeout=300)
            analysis_result = future_analysis.result(timeout=300)

        # Validate outputs
        if not vocal_path.exists():
            raise RuntimeError("Vocal separation failed - no output file")
        if not analysis_result:
            raise ValueError("Audio analysis failed")

        return {
            'results': analysis_result,
            'vocal_path': str(vocal_path),
            'backing_path': str(backing_path),
            'process_id': process_id
        }

    except Exception as e:
        # Cleanup failed outputs
        if output_dir.exists():
            for f in output_dir.iterdir():
                f.unlink()
            output_dir.rmdir()
        raise e


@st.cache_data
def analyze_audio(file_path, _cache):
    """Improved audio analysis with safe caching"""
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")

        # Generate stable cache key
        file_stat = file_path.stat()
        cache_key = hashlib.md5(
            f"{file_path.name}-{file_stat.st_size}-{file_stat.st_mtime}".encode()
        ).hexdigest()

        if cached := _cache.get_cached_result(cache_key):
            if all(k in cached for k in ['key', 'bpm', 'additional_info']):
                return cached

        # Load and validate audio
        loader = AudioLoader()
        y, sr = loader.load_audio(str(file_path))
        if y is None or sr is None:
            raise ValueError("Failed to load audio data")

        # Perform analysis
        analyzer = AudioAnalyzer()
        results = {
            'key': analyzer.detect_key(y, sr),
            'bpm': analyzer.detect_bpm(y, sr),
            'additional_info': analyzer.get_additional_info(y, sr)
        }

        _cache.cache_result(cache_key, results)
        return results

    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return None


def main():
    """Main application flow"""
    st.title("🎵 Audio Analyzer")
    create_temp_dir()

    if 'separator' not in st.session_state:
        st.session_state.separator = VocalSeparator()
        st.session_state.cache = ResultsCache()
        # Add dummy attributes for Streamlit hashing
        st.session_state.separator._cache_hash = id(st.session_state.separator)
        st.session_state.cache._cache_hash = id(st.session_state.cache)

    tab_upload, tab_youtube = st.tabs(["📤 File Upload", "▶️ YouTube"])

    with tab_upload:
        uploaded_file = st.file_uploader("Choose audio file", type=['mp3', 'wav'])
        if uploaded_file:
            try:
                # Create temp directory with proper path handling
                temp_dir = os.path.abspath(os.path.join("temp", "uploads"))
                os.makedirs(temp_dir, exist_ok=True)

                # Sanitize filename and create full path
                safe_name = secure_filename(uploaded_file.name)
                temp_path = os.path.join(temp_dir, safe_name)

                # Write file with verification
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Verify file exists before processing
                if not os.path.exists(temp_path):
                    raise FileNotFoundError(f"Failed to save uploaded file to {temp_path}")

                # Clear previous results
                st.session_state.processed = False

                # Process file with progress
                with st.spinner("🔍 Processing audio..."):
                    processing_results = process_audio(
                        temp_path,
                        st.session_state.separator,
                        st.session_state.cache
                    )

                    if processing_results and processing_results['results']:
                        st.session_state.update({
                            'results': processing_results['results'],
                            'vocal_path': processing_results['vocal_path'],
                            'backing_path': processing_results['backing_path'],
                            'processed': True
                        })
                        st.experimental_rerun()
                    else:
                        st.error("Processing failed to return valid results")

            except Exception as e:
                st.error(f"❌ Processing error: {str(e)}")
                # Clean up failed files
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)

        if st.session_state.get('processed', False):
            st.success("✅ Processing completed!")
            display_analysis_results(st.session_state.results)
            display_download_section()

    with tab_youtube:
        yt_url = st.text_input("YouTube URL:", key="yt_url")
        if yt_url and st.button("Process YouTube", key="yt_button"):
            with st.spinner("🌐 Downloading audio..."):
                try:
                    audio_path = st.session_state.yt_downloader.download_audio(yt_url, "temp")
                    with st.spinner("🔍 Processing audio..."):
                        processed_data = process_audio(
                            audio_path,
                            st.session_state.separator,
                            st.session_state.cache
                        )

                        if processed_data and processed_data['results']:
                            st.session_state.update({
                                'yt_results': processed_data['results'],
                                'yt_vocal_path': processed_data['vocal_path'],
                                'yt_backing_path': processed_data['backing_path']
                            })
                            st.success("✅ Processing completed!")
                            display_analysis_results(st.session_state.yt_results)
                            display_yt_download_section()
                        else:
                            st.error("YouTube processing failed")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


def display_analysis_results(results):
    """Display analysis results with error handling"""
    st.subheader("Analysis Results")

    if not results:
        st.error("❌ No analysis results available")
        return

    try:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🎶 Key", results.get('key', 'N/A'), help="Detected musical key")
        with col2:
            st.metric("🥁 BPM", results.get('bpm', 'N/A'), help="Beats per minute")

        with st.expander("📊 Detailed Analysis"):
            if 'additional_info' in results:
                for k, v in results['additional_info'].items():
                    st.markdown(f"**{k.replace('_', ' ').title()}:** `{v}`")
            else:
                st.warning("No additional information available")

    except Exception as e:
        st.error(f"Error displaying results: {str(e)}")


def display_download_section():
    """Display file upload download section"""
    st.subheader("🎧 Download Separated Tracks")

    if not all([st.session_state.get('vocal_path'),
                st.session_state.get('backing_path')]):
        st.warning("Separation in progress...")
        return

    col1, col2 = st.columns(2)
    with col1:
        if os.path.exists(st.session_state.vocal_path):
            st.download_button(
                "⬇️ Download Vocals",
                b"".join(read_file_chunked(st.session_state.vocal_path)),
                file_name="vocals.wav",
                mime="audio/wav",
                key="dl_vocal"
            )
    with col2:
        if os.path.exists(st.session_state.backing_path):
            st.download_button(
                "⬇️ Download Instrumental",
                b"".join(read_file_chunked(st.session_state.backing_path)),
                file_name="accompaniment.wav",
                mime="audio/wav",
                key="dl_backing"
            )


def display_yt_download_section():
    """Display YouTube download section"""
    st.subheader("🎧 YouTube Downloads")

    if not all([st.session_state.get('yt_vocal_path'),
                st.session_state.get('yt_backing_path')]):
        st.warning("Separation in progress...")
        return

    col1, col2 = st.columns(2)
    with col1:
        if os.path.exists(st.session_state.yt_vocal_path):
            st.download_button(
                "⬇️ YouTube Vocals",
                b"".join(read_file_chunked(st.session_state.yt_vocal_path)),
                file_name="yt_vocals.wav",
                mime="audio/wav",
                key="yt_dl_vocal"
            )
    with col2:
        if os.path.exists(st.session_state.yt_backing_path):
            st.download_button(
                "⬇️ YouTube Instrumental",
                b"".join(read_file_chunked(st.session_state.yt_backing_path)),
                file_name="yt_accompaniment.wav",
                mime="audio/wav",
                key="yt_dl_backing"
            )


if __name__ == "__main__":
    main()