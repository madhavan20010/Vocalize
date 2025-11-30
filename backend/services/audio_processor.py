import os
import yt_dlp
import demucs.separate
import librosa
import numpy as np
import shlex
import subprocess
from pathlib import Path
import json
import webvtt

class AudioProcessor:
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.last_subtitle_path = None # Initialize subtitle path

    def download_youtube(self, url: str) -> str:
        """
        Downloads audio from YouTube URL.
        Returns the path to the downloaded file.
        """
        # Download options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            # Attempt to download subtitles, but don't fail if missing
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'quiet': True,
            # Use Android client to avoid 403s
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # FFmpeg conversion changes extension to .wav
            final_path = os.path.splitext(filename)[0] + ".wav"
            
            if not os.path.exists(final_path):
                raise Exception(f"Download failed: File {final_path} not found")
            
            # Store subtitle path if it exists
            self.last_subtitle_path = None
            base_path = os.path.splitext(filename)[0]
            
            # Check for any vtt file with the same base name
            for f in os.listdir(self.output_dir):
                if f.endswith(".vtt") and os.path.splitext(f)[0].startswith(os.path.basename(base_path)):
                    self.last_subtitle_path = os.path.join(self.output_dir, f)
                    break
                    
            return final_path

    def separate_stems(self, audio_path: str) -> dict:
        """
        Separates audio into 4 stems (vocals, drums, bass, other) using Demucs.
        Returns a dictionary of paths to the stems.
        """
        # Using the demucs command line interface via subprocess for simplicity
        # as the API can be complex to set up with model loading in the same process
        # if not managed carefully.
        
        # Output structure of demucs: <out>/htdemucs/<track_name>/<stem>.wav
        
        track_name = Path(audio_path).stem
        stem_dir = self.output_dir / "htdemucs" / track_name
        
        # Check if stems already exist
        vocals_path = stem_dir / "vocals.wav"
        drums_path = stem_dir / "drums.wav"
        bass_path = stem_dir / "bass.wav"
        other_path = stem_dir / "other.wav"
        
        if vocals_path.exists() and drums_path.exists() and bass_path.exists() and other_path.exists():
            print(f"Stems already exist for {track_name}, skipping separation.")
            return {
                "vocals": str(vocals_path),
                "drums": str(drums_path),
                "bass": str(bass_path),
                "other": str(other_path)
            }
        
        # Use sys.executable to ensure we use the venv's python and demucs module
        import sys
        cmd = [sys.executable, "-m", "demucs", "-n", "htdemucs", "--out", str(self.output_dir), str(audio_path)]
        subprocess.run(cmd, check=True)
        
        return {
            "vocals": str(vocals_path),
            "drums": str(drums_path),
            "bass": str(bass_path),
            "other": str(other_path)
        }

    def detect_key(self, audio_path: str) -> str:
        """
        Detects the key of the audio using Librosa Chroma features.
        """
        y, sr = librosa.load(audio_path)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Sum chroma over time
        chroma_sum = np.sum(chroma, axis=1)
        
        # Major and Minor profiles
        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        # Correlate
        major_corrs = []
        minor_corrs = []
        
        for i in range(12):
            major_corrs.append(np.corrcoef(np.roll(chroma_sum, -i), major_profile)[0, 1])
            minor_corrs.append(np.corrcoef(np.roll(chroma_sum, -i), minor_profile)[0, 1])
            
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        best_major_idx = np.argmax(major_corrs)
        best_minor_idx = np.argmax(minor_corrs)
        
        if major_corrs[best_major_idx] > minor_corrs[best_minor_idx]:
            return f"{key_names[best_major_idx]} Major"
        else:
            return f"{key_names[best_minor_idx]} Minor"

    def google_search_key_validation(self, song_name: str) -> str:
        """
        Placeholder for Google Search validation.
        In a real app, this would use a search API or scraper.
        """
        # TODO: Implement Google Search scraping
        return "Unknown"

    def transcribe_audio(self, audio_path: str) -> list:
        """
        Returns lyrics with timestamps.
        Prioritizes YouTube subtitles if available (fast & accurate).
        Falls back to OpenAI Whisper (slower).
        """
        # 0. Try Web Scraping (User Request: "Get from internet")
        try:
            # Extract track name from path (e.g., "Maruvaarthai...")
            path_parts = Path(audio_path).parts
            if "htdemucs" in path_parts:
                track_name = path_parts[-2]
                # Clean track name (remove "Lyric Video", etc.)
                # 1. Remove common suffixes
                clean_name = track_name.replace("Lyric Video", "").replace("Official Video", "").replace("Video Song", "")
                # 2. Split by | and take first part
                if "｜" in clean_name: # Full-width pipe
                    clean_name = clean_name.split("｜")[0]
                if "|" in clean_name: # Normal pipe
                    clean_name = clean_name.split("|")[0]
                # 3. Split by - and take first part (often Artist - Title or Title - Artist)
                # But sometimes it's "Title - Movie", so taking first part is usually safe for lyrics search
                if "-" in clean_name:
                    clean_name = clean_name.split("-")[0]
                
                clean_name = clean_name.strip()
                
                print(f"Attempting to fetch lyrics from web for: {clean_name}")
                from services.lyrics_scraper import LyricsScraper
                scraper = LyricsScraper()
                web_lyrics, source_url = scraper.fetch_lyrics(clean_name)
                
                if web_lyrics:
                    print(f"Found lyrics from web: {source_url}")
                    # Convert to simple word list format for frontend compatibility
                    # We don't have timestamps, so we'll fake them or just return words
                    words = []
                    for i, word in enumerate(web_lyrics.split()):
                        words.append({
                            "word": word,
                            "start": i * 0.5, # Fake timing
                            "end": (i * 0.5) + 0.4
                        })
                    return words
        except Exception as e:
            print(f"Web scraping failed: {e}")

        # 1. Try parsing Subtitles
        # Check in-memory path first
        if hasattr(self, 'last_subtitle_path') and self.last_subtitle_path and os.path.exists(self.last_subtitle_path):
            print(f"Using subtitles from {self.last_subtitle_path}")
            return self._parse_vtt(self.last_subtitle_path)
            
        # Check on disk based on audio path
        # audio_path is usually temp_audio/htdemucs/Title/vocals.wav
        # VTT is usually temp_audio/Title.en.vtt
        try:
            path_parts = Path(audio_path).parts
            if "htdemucs" in path_parts:
                # Go up to temp_audio
                # parts: (..., temp_audio, htdemucs, Title, vocals.wav)
                track_name = path_parts[-2]
                temp_dir = Path(audio_path).parents[2] # temp_audio
                
                # Look for VTT files starting with track_name
                # Priority: .ta.vtt (Tamil) > .en.vtt (English) > .vtt (Generic)
                temp_files = os.listdir(temp_dir)
                
                # 1. Check for Tamil VTT
                for f in temp_files:
                    if f.endswith(".ta.vtt") and f.startswith(track_name[:20]):
                        vtt_path = os.path.join(temp_dir, f)
                        print(f"Found Tamil VTT on disk: {vtt_path}")
                        return self._parse_vtt(vtt_path)
                        
                # 2. Check for English/Generic VTT
                for f in temp_files:
                    if f.endswith(".vtt") and f.startswith(track_name[:20]):
                        vtt_path = os.path.join(temp_dir, f)
                        print(f"Found VTT on disk: {vtt_path}")
                        return self._parse_vtt(vtt_path)
        except Exception as e:
            print(f"Error searching for VTT: {e}")

        # 2. Fallback to Whisper
        print(f"No subtitles found. Using Whisper on {audio_path}...")
        import whisper
        
        try:
            # Load model (download on first run)
            # 'small' is better for isolated vocals than 'base'
            print("Loading Whisper model (small)...")
            model = whisper.load_model("small")
            
            # Transcribe with word timestamps
            print("Starting transcription...")
            result = model.transcribe(audio_path, word_timestamps=True)
            print(f"Transcription complete. Segments: {len(result['segments'])}")
            
            # Process result into a flat list of words for easier frontend sync
            words = []
            for segment in result['segments']:
                for word in segment['words']:
                    words.append({
                        'word': word['word'].strip(),
                        'start': word['start'],
                        'end': word['end']
                    })
            
            print(f"Extracted {len(words)} words.")
            return words
        except Exception as e:
            print(f"Whisper error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_vtt(self, vtt_path: str) -> list:
        """
        Parses a VTT subtitle file into word-level chunks.
        Note: VTT usually gives line-level timestamps. We will split lines into words
        and interpolate timestamps for a smoother effect, or just return lines.
        For Karaoke, line-level is often okay, but we want word-level if possible.
        """
        words = []
        
        try:
            for caption in webvtt.read(vtt_path):
                start = caption.start_in_seconds
                end = caption.end_in_seconds
                text = caption.text.strip()
                
                # Split into words and distribute time evenly
                # This is an approximation but much faster than Whisper
                caption_words = text.split()
                if not caption_words:
                    continue
                    
                duration = end - start
                word_duration = duration / len(caption_words)
                
                for i, word in enumerate(caption_words):
                    words.append({
                        'word': word,
                        'start': start + (i * word_duration),
                        'end': start + ((i + 1) * word_duration)
                    })
        except Exception as e:
            print(f"Error parsing VTT: {e}")
            return []
            
        return words
