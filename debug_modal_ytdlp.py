import modal
import subprocess

image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg", "git")
    .pip_install("yt-dlp")
)

app = modal.App("debug-ytdlp", image=image)

@app.function()
def debug_download(url: str):
    print(f"Testing download for {url}")
    try:
        # Run with verbose output
        cmd = ["yt-dlp", "-v", "-x", "--audio-format", "wav", "-o", "/tmp/test.wav", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        if result.returncode != 0:
            print(f"Failed with code {result.returncode}")
        else:
            print("Success!")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # This part runs locally when we call `modal run`
    pass
