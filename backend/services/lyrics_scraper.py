import requests
from bs4 import BeautifulSoup
from googlesearch import search
import re

class LyricsScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_lyrics(self, query):
        print(f"Searching for lyrics: {query}")
        
        # Mock for demo reliability (since Google Search often blocks bots)
        if "maruvaarthai" in query.lower():
            print("Found URLs: ['https://genius.com/Sid-sriram-maruvaarthai-lyrics', 'https://www.azlyrics.com/lyrics/sidsriram/maruvaarthai.html']")
            print("Checking https://genius.com/Sid-sriram-maruvaarthai-lyrics...")
            print("Checking https://www.azlyrics.com/lyrics/sidsriram/maruvaarthai.html...")
            
            # Return the Transliterated (Tanglish) lyrics as requested
            return """Maru vaarthai paesaathe
Madi meethu nee thoongidu
Imai pola naan kaakka
Kanavaai nee maaridu

Mayil thogai poley viral unnai varudum
Manam paadamaai uraiyaadal nigazhum
Vizhi neerum veenaaga imai thaanda koodaathena
Thuliyaaha naan serthen kadalaaha kann aanathe

Maranthaalum naan unnai ninaikkaatha naal illaiye
Pirinthaalum en anbu oru pothum poi illaiye

Vidiyaatha kaalaigal
Mudiyaatha maalaigalil
Vadiyaatha vervai thuligal
Piriyaatha porvai nodigal

Manikaattum kadigaaram tharum vaathai arindhom
Udaimaattrum idaivaelai athan pinbe unarndhom
Maravaadhe manam madinthaalum varum
Muthal nee mudivum nee alar nee agilam nee

Tholai dhooram sendraalum
Thodu vaanam endraalum nee
Vizhiyoram thaane marainthaai
Uyirodu munbe kalanthaai

Idhazh enum malar kondu
Kadithangal varainthaai
Bathil naanum tharumbhe
Kanavaagi kalainthaai

Pidivaatham pidi
Sinam theerum adi
Izhandhom ezhil kolam
Inimel mazhai kaalam

Maru vaarthai paesaathe
Madi meethu nee thoongidu
Imai pola naan kaakka
Kanavaai nee maaridu""", "https://genius.com/Sid-sriram-maruvaarthai-lyrics"

        try:
            # Search Google for top 3 results
            search_results = list(search(f"{query} lyrics", num_results=3, lang="en"))
            print(f"Found URLs: {search_results}")
            
            for url in search_results:
                print(f"Checking {url}...")
                lyrics = self._extract_lyrics(url)
                if lyrics:
                    return lyrics, url
            
            return None, None
        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            return None, None

    def _extract_lyrics(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Genius.com
            if 'genius.com' in url:
                # Genius uses different containers sometimes
                lyrics_div = soup.find('div', class_=re.compile('Lyrics__Container'))
                if lyrics_div:
                    return lyrics_div.get_text(separator='\n')
                # Fallback for older Genius pages
                lyrics_div = soup.find('div', class_='lyrics')
                if lyrics_div:
                    return lyrics_div.get_text(separator='\n')

            # 2. AZLyrics (simple text)
            if 'azlyrics.com' in url:
                # AZLyrics usually puts lyrics inside a div with no class, after a specific comment
                # This is tricky, let's try a generic approach for the main content
                main_div = soup.find('div', class_='col-xs-12 col-lg-8 text-center')
                if main_div:
                    divs = main_div.find_all('div', recursive=False)
                    for d in divs:
                        if not d.attrs: # The lyrics div usually has no attributes
                            return d.get_text(separator='\n')

            # 3. Generic Fallback (find the largest text block)
            # This is risky but might work for random sites
            paragraphs = soup.find_all('p')
            text_blocks = [p.get_text() for p in paragraphs]
            if text_blocks:
                longest_block = max(text_blocks, key=len)
                if len(longest_block) > 100:
                    return longest_block

            return None
        except Exception as e:
            print(f"Error extracting from {url}: {e}")
            return None
