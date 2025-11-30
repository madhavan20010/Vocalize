import webvtt
import os

vtt_path = "temp_audio/Maruvaarthai - Lyric Video ｜ Enai Noki Paayum Thota ｜ Dhanush ｜ Darbuka Siva ｜ Gautham Menon.en.vtt"

print(f"Checking {vtt_path}...")
if not os.path.exists(vtt_path):
    print("File not found!")
    exit(1)

try:
    print("Parsing with webvtt...")
    captions = webvtt.read(vtt_path)
    print(f"Found {len(captions)} captions.")
    
    lyrics = []
    for caption in captions:
        # Clean up text
        text = caption.text.strip().replace('\n', ' ')
        if not text:
            continue
            
        # Parse timestamps (HH:MM:SS.mmm -> seconds)
        def parse_time(t_str):
            h, m, s = t_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
            
        start = parse_time(caption.start)
        end = parse_time(caption.end)
        
        # Split into words for word-level sync simulation
        words = text.split(' ')
        duration = end - start
        word_duration = duration / len(words)
        
        current_time = start
        for word in words:
            lyrics.append({
                'word': word,
                'start': current_time,
                'end': current_time + word_duration
            })
            current_time += word_duration
            
    print(f"Extracted {len(lyrics)} words.")
    print("First 5 words:", lyrics[:5])

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
