import requests
import json
import sys

def test_transcribe():
    # 1. First, we need a file to transcribe. 
    # We can try to use an existing file if one was downloaded, or download a new one.
    # For this test, let's assume we can hit the /process endpoint first with a short video.
    
    base_url = "http://localhost:8000"
    
    # Short video with captions (Rick Astley - Never Gonna Give You Up is too long, let's use something shorter if possible, 
    # but for now let's stick to a known URL and just check if we can get the path)
    # Actually, let's just check if we can hit /transcribe with a dummy path to see error handling,
    # or if we can find a file in temp_audio.
    
    print("Testing /transcribe endpoint...")
    
    # Target Maruvaarthai vocals
    import glob
    matches = glob.glob("temp_audio/htdemucs/*Maruvaarthai*/vocals.wav")
    if matches:
        vocals_path = matches[0]
    else:
        print("Could not find vocals for Maruvaarthai")
        return

    # Construct the relative path expected by the backend
    # Backend expects "temp_audio/..." but we need to send the URL that maps to it.
    # The backend splits by "/audio/", so:
    # input: http://localhost:8000/audio/htdemucs/rpIlP6pI8fo/vocals.wav
    # processed: temp_audio/htdemucs/rpIlP6pI8fo/vocals.wav
    
    # We need to be careful about the path construction.
    # If vocals_path is "temp_audio/htdemucs/...", we want "htdemucs/..."
    
    rel_path = vocals_path.replace("temp_audio/", "")
    audio_url = f"http://localhost:8000/audio/{rel_path}"
    
    print(f"Requesting transcription for: {audio_url}")
    
    try:
        res = requests.post(
            f"{base_url}/transcribe",
            json={"audio_url": audio_url},
            headers={"Content-Type": "application/json"}
        )
        
        if res.status_code == 200:
            data = res.json()
            lyrics = data.get("lyrics", [])
            print(f"Success! Found {len(lyrics)} lyric segments.")
            if lyrics:
                print("Sample:", lyrics[:3])
        else:
            print(f"Failed with status {res.status_code}: {res.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_transcribe()
