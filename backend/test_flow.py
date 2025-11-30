import sys
import os
from services.audio_processor import AudioProcessor

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

def test_full_flow():
    print("--- Starting End-to-End Test ---")
    
    # 1. Setup
    output_dir = "temp_audio_test"
    os.makedirs(output_dir, exist_ok=True)
    processor = AudioProcessor(output_dir=output_dir)
    
    # 2. Download (Using the user's specific link)
    youtube_url = "https://youtu.be/k3g_WjLCsXM?si=VM0gWeXkzXJx_N3s"
    print(f"1. Attempting to download: {youtube_url}")
    
    try:
        file_path = processor.download_youtube(youtube_url)
        print(f"   Success! Downloaded to: {file_path}")
    except Exception as e:
        print(f"   FAILED to download: {e}")
        return

    # 3. Key Detection
    print("2. Detecting Key...")
    try:
        key = processor.detect_key(file_path)
        print(f"   Success! Detected Key: {key}")
    except Exception as e:
        print(f"   Warning: Key detection failed ({e})")

    # 4. Stem Separation
    print("3. Separating Stems (Demucs)...")
    try:
        stems = processor.separate_stems(file_path)
        print("   Success! Stems generated:")
        for name, path in stems.items():
            print(f"   - {name}: {path}")
    except Exception as e:
        print(f"   FAILED to separate stems: {e}")
        return

    print("\n--- Test Completed Successfully ---")

if __name__ == "__main__":
    test_full_flow()
