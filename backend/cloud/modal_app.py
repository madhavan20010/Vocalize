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
        "ffmpeg-python",
        "fastapi",
        "uvicorn",
        "python-multipart"
    )
    .add_local_dir("backend", remote_path="/root/backend", ignore=["venv", "__pycache__", "*.pyc", ".DS_Store"])
)

app = modal.App("vocalize-cloud", image=image)

# Mount not needed as we added to image
# backend_mount = ...

@app.function(
    gpu="a10g",  # Use A10G GPU for fast processing
    timeout=600, # 10 minutes timeout
    secrets=[modal.Secret.from_name("supabase-secret")], # Requires SUPABASE_URL and SUPABASE_KEY
    # mounts=[backend_mount] # Code is in image
)
def process_audio_cloud(youtube_url: str = None, audio_url: str = None):
    import subprocess
    import shutil
    import requests
    from pathlib import Path
    # Import from the mounted backend package
    from backend.cloud.supabase_client import SupabaseManager

    print(f"Processing on Cloud GPU...")
    
    # Setup paths
    output_dir = Path("/tmp/audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Download
    if youtube_url:
        print(f"Downloading YouTube: {youtube_url}")
        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "wav",
            "-o", str(output_dir / "%(title)s.%(ext)s"),
            youtube_url
        ]
        subprocess.run(cmd, check=True)
    elif audio_url:
        print(f"Downloading File: {audio_url}")
        response = requests.get(audio_url)
        # Try to get filename from header or use default
        filename = "uploaded_song.wav"
        with open(output_dir / filename, "wb") as f:
            f.write(response.content)
    else:
        return {"status": "error", "message": "No input provided"}
    
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
        "key": "C Major" # Placeholder
    }

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("supabase-secret")],
    # mounts=[backend_mount] # Code is in image
    timeout=600
)
@modal.asgi_app()
def fastapi_app():
    # Set environment variables for Cloud Mode
    os.environ["USE_CLOUD_PROCESSING"] = "true"
    
    # Import inside the function to avoid local import errors
    from backend.main import app as web_app
    return web_app
