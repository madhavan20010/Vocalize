import os
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment

class ExportService:
    def __init__(self):
        self.output_dir = "exports"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def mix_and_export(self, stems, volumes, pitch_shift, format="mp3"):
        """
        Mixes stems with volume and pitch adjustments.
        stems: dict of {stem_name: file_path}
        volumes: dict of {stem_name: volume_float (0.0-1.0)}
        pitch_shift: float (semitones)
        format: "mp3" or "mp4" (audio only)
        """
        try:
            print(f"Exporting with volumes={volumes}, pitch={pitch_shift}")
            
            mixed_audio = None
            sr = 44100 # Standard sample rate

            for stem_name, file_path in stems.items():
                if not os.path.exists(file_path):
                    continue
                
                vol = volumes.get(stem_name, 1.0)
                if vol == 0:
                    continue # Skip silent tracks

                # Load audio
                y, _ = librosa.load(file_path, sr=sr)

                # Apply Pitch Shift (if needed)
                # Note: Pitch shifting is expensive. 
                if pitch_shift != 0:
                    # Use librosa for high quality time-stretching pitch shift
                    y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift)

                # Apply Volume
                y = y * vol

                # Mix
                if mixed_audio is None:
                    mixed_audio = y
                else:
                    # Ensure lengths match
                    if len(y) > len(mixed_audio):
                        mixed_audio = np.pad(mixed_audio, (0, len(y) - len(mixed_audio)))
                    elif len(y) < len(mixed_audio):
                        y = np.pad(y, (0, len(mixed_audio) - len(y)))
                    
                    mixed_audio = mixed_audio + y

            if mixed_audio is None:
                return None

            # Normalize to prevent clipping
            max_val = np.max(np.abs(mixed_audio))
            if max_val > 1.0:
                mixed_audio = mixed_audio / max_val

            # Save to temporary WAV first
            temp_wav = os.path.join(self.output_dir, "temp_mix.wav")
            sf.write(temp_wav, mixed_audio, sr)

            # Convert to requested format using pydub (which uses ffmpeg)
            output_filename = f"mix_{int(os.path.getmtime(temp_wav))}.{format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            audio = AudioSegment.from_wav(temp_wav)
            audio.export(output_path, format="mp3" if format == "mp4" else format) # MP4 audio is usually AAC/MP3 container, but user asked for mp4 file. ffmpeg can wrap mp3 in mp4 or just save as mp3.
            # If format is mp4, we should probably output an audio-only mp4 (m4a) or just mp3.
            # User asked for "mp3 or mp4".
            if format == "mp4":
                 # Export as mp4 (audio only)
                 audio.export(output_path, format="mp4")
            else:
                 audio.export(output_path, format="mp3")

            # Cleanup temp
            if os.path.exists(temp_wav):
                os.remove(temp_wav)

            return output_path

        except Exception as e:
            print(f"Error exporting: {e}")
            return None
