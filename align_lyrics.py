import webvtt
import sys

def align_lyrics(vtt_path, lyrics_path, output_path):
    # Read VTT
    captions = webvtt.read(vtt_path)
    print(f"Read {len(captions)} captions from VTT.")
    
    # Read Lyrics
    with open(lyrics_path, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    print(f"Read {len(lines)} lines of lyrics.")
    
    # Naive Alignment:
    # If we have fewer lyric lines than captions, we stretch them.
    # If we have more, we combine them.
    # Actually, let's just cycle or fill.
    
    # Better strategy for this specific song:
    # The VTT has 54 lines. The lyrics have ~34 lines.
    # We can try to map them proportionally.
    
    ratio = len(captions) / len(lines)
    
    new_captions = []
    lyric_idx = 0
    
    for i, caption in enumerate(captions):
        # Calculate which lyric line corresponds to this caption index
        target_lyric_idx = int(i / ratio)
        
        if target_lyric_idx < len(lines):
            text = lines[target_lyric_idx]
        else:
            text = ""
            
        # Create new caption
        new_caption = webvtt.Caption(
            start=caption.start,
            end=caption.end,
            text=text
        )
        new_captions.append(new_caption)
        
    # Save
    vtt = webvtt.WebVTT()
    vtt.captions = new_captions
    vtt.save(output_path)
    print(f"Saved aligned VTT to {output_path}")

if __name__ == "__main__":
    vtt_path = "temp_audio/Maruvaarthai - Lyric Video ｜ Enai Noki Paayum Thota ｜ Dhanush ｜ Darbuka Siva ｜ Gautham Menon.en.vtt"
    lyrics_path = "tamil_lyrics.txt"
    output_path = "temp_audio/Maruvaarthai - Lyric Video ｜ Enai Noki Paayum Thota ｜ Dhanush ｜ Darbuka Siva ｜ Gautham Menon.ta.vtt"
    
    align_lyrics(vtt_path, lyrics_path, output_path)
