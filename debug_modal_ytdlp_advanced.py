import modal
import subprocess

image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg", "git")
    .pip_install("yt-dlp")
)

app = modal.App("debug-ytdlp-advanced", image=image)

@app.function()
def debug_download_advanced(url: str):
    print(f"Testing advanced download for {url}")
    
    configs = [
        # 1. Force IPv4
        ["yt-dlp", "--force-ipv4", "-v", "-x", "--audio-format", "wav", "-o", "/tmp/test_ipv4.wav", url],
        # 2. Android Client
        ["yt-dlp", "--extractor-args", "youtube:player_client=android", "-v", "-x", "--audio-format", "wav", "-o", "/tmp/test_android.wav", url],
        # 3. Web Client
        ["yt-dlp", "--extractor-args", "youtube:player_client=web", "-v", "-x", "--audio-format", "wav", "-o", "/tmp/test_web.wav", url],
        # 4. iOS Client
        ["yt-dlp", "--extractor-args", "youtube:player_client=ios", "-v", "-x", "--audio-format", "wav", "-o", "/tmp/test_ios.wav", url],
    ]

    for i, cmd in enumerate(configs):
        print(f"\n--- Test {i+1}: {' '.join(cmd)} ---")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("SUCCESS!")
                return # Stop on first success
            else:
                print(f"FAILED (Code {result.returncode})")
                # Print last few lines of stderr
                print("\n".join(result.stderr.splitlines()[-10:]))
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    pass
