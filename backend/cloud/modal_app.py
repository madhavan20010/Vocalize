import modal
import os
import sys
import time

# Define the Modal Image with dependencies
image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg", "git")
    .pip_install(
        "yt-dlp",
        "demucs",
        "supabase",
        "torch",
        "torchaudio",
        "ffmpeg-python"
    )
    .add_local_file("backend/cloud/supabase_client.py", remote_path="/root/supabase_client.py")
)

app = modal.App("vocalize-cloud", image=image)

@app.function(
    gpu="a10g",  # Use A10G GPU for fast processing
    timeout=600, # 10 minutes timeout
    secrets=[modal.Secret.from_name("supabase-secret")] # Requires SUPABASE_URL and SUPABASE_KEY
)
def process_audio_cloud(youtube_url: str):
    import subprocess
    import shutil
    from pathlib import Path
    from supabase_client import SupabaseManager

    print(f"Processing {youtube_url} on Cloud GPU...")
    
    # Setup paths
    output_dir = Path("/tmp/audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Download with yt-dlp
    print("Downloading...")
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "wav",
        "-o", str(output_dir / "%(title)s.%(ext)s"),
        youtube_url
    ]
    subprocess.run(cmd, check=True)
    
    # Find downloaded file
    downloaded_file = next(output_dir.glob("*.wav"))
    print(f"Downloaded: {downloaded_file}")
    
    # 2. Run Demucs
    print("Separating stems...")
    # Demucs command: demucs -n htdemucs --two-stems=vocals -o <out> <in>
    # We want all 4 stems
    cmd = [
        "demucs",
        "-n", "htdemucs",
        "-o", str(output_dir / "separated"),
        str(downloaded_file)
    ]
    subprocess.run(cmd, check=True)
    
    # 3. Upload to Supabase
    print("Uploading to Supabase...")
    sb = SupabaseManager()
    if not sb.is_enabled():
        return {"status": "error", "message": "Supabase not configured in Cloud"}
        
    # Structure: separated/htdemucs/<song_name>/<stem>.wav
    model_dir = output_dir / "separated" / "htdemucs"
    song_dir = next(model_dir.iterdir())
    song_name = song_dir.name
    
    stems = {}
    timestamp = int(time.time())
    
    # Upload original
    orig_path = f"uploads/{timestamp}_{song_name}.wav"
    orig_url = sb.upload_file(str(downloaded_file), "audio", orig_path)
    
    # Upload stems
    for stem in ["vocals", "drums", "bass", "other"]:
        stem_file = song_dir / f"{stem}.wav"
        if stem_file.exists():
            remote_path = f"stems/{timestamp}_{song_name}/{stem}.wav"
            url = sb.upload_file(str(stem_file), "audio", remote_path)
            stems[stem] = url
            
    return {
        "status": "success",
        "stems": stems,
        "original_file": orig_url,
        "key": "C Major" # Placeholder, need to run key detection logic or port it
    }

if __name__ == "__main__":
    # Local test
    pass
