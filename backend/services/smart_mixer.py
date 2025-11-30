import librosa
import numpy as np
import soundfile as sf
from pedalboard import Pedalboard, Compressor, Reverb, HighpassFilter, LowpassFilter, Gain, PitchShift
from pedalboard.io import AudioFile

class SmartMixer:
    def __init__(self):
        pass

    def analyze_reference(self, reference_path: str):
        """
        Analyzes the reference vocal track to extract mixing parameters.
        Returns a dictionary of parameters (brightness, dynamics, reverb_amount).
        """
        y, sr = librosa.load(reference_path)
        
        # 1. Brightness (Spectral Centroid)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        brightness = np.mean(centroid)
        
        # 2. Dynamics (RMS)
        rms = librosa.feature.rms(y=y)
        dynamic_range = np.max(rms) - np.min(rms)
        
        # 3. Reverb (Estimate based on decay - simplified)
        # This is hard to estimate accurately without clean dry/wet, 
        # but we can look at the tail energy.
        
        return {
            "brightness": float(brightness),
            "dynamic_range": float(dynamic_range),
            "reverb_estimate": 0.3 # Placeholder for complex reverb estimation
        }

    def apply_mix(self, input_path: str, output_path: str, reference_params: dict, strength: float = 1.0):
        """
        Applies mixing effects to the input audio based on reference parameters.
        Strength (0.0 to 1.0) controls the intensity of the match.
        """
        # Read audio
        with AudioFile(input_path) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate

        # Create Board
        board = Pedalboard()
        
        # 1. EQ (Brightness match)
        # If reference is bright, boost highs.
        if reference_params["brightness"] > 3000:
            board.append(HighpassFilter(cutoff_frequency_hz=200)) # Clean mud
            # In a real app, we'd use a parametric EQ here
        
        # 2. Compression (Dynamics match)
        # If reference has low dynamic range, compress heavily.
        threshold = -20.0 * strength
        ratio = 2.0 + (2.0 * strength)
        board.append(Compressor(threshold_db=threshold, ratio=ratio))
        
        # 3. Reverb
        room_size = reference_params["reverb_estimate"] * strength
        if room_size > 0:
            board.append(Reverb(room_size=room_size, wet_level=0.3 * strength))

        # Process
        processed = board(audio, samplerate)

        # Save
        with AudioFile(output_path, 'w', samplerate, processed.shape[0]) as f:
            f.write(processed)
            
        return output_path

    def apply_autotune(self, input_path: str, output_path: str, key: str, strength: float = 1.0):
        """
        Simple pitch correction.
        Note: High quality autotune is complex. We will use a simple pitch shifter 
        guided by the key for this MVP, or just a static pitch shift if requested.
        
        Real autotune requires a vocoder or pitch correction library like Autotalent.
        For now, we will implement a simple 'PitchShift' if the user wants to change key,
        as 'Auto-tune' usually implies correcting to nearest note.
        """
        # For this MVP, we will just implement the Pitch Shift feature requested
        # "reduce the pitch by how many every semitones I want to"
        
        # If strength is treated as semitones for shifting:
        semitones = int(strength)
        
        with AudioFile(input_path) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate
            
        board = Pedalboard([
            PitchShift(semitones=semitones)
        ])
        
        processed = board(audio, samplerate)
        
        with AudioFile(output_path, 'w', samplerate, processed.shape[0]) as f:
            f.write(processed)
            
        return output_path

    def align_audio(self, input_path: str, output_path: str, start_time: float):
        """
        Pads the beginning of the audio file with silence corresponding to start_time.
        """
        # Load audio
        y, sr = librosa.load(input_path, sr=None) # Keep original SR
        
        # Calculate silence samples
        num_silent_samples = int(start_time * sr)
        
        if num_silent_samples > 0:
            silence = np.zeros(num_silent_samples)
            # Concatenate
            y_aligned = np.concatenate((silence, y))
        else:
            y_aligned = y
            
        # Save
        sf.write(output_path, y_aligned, sr)
        return output_path
