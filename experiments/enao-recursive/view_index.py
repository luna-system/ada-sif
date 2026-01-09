
import re

INDEX_FILE = '/home/luna/Code/ada/ada-sif/experiments/enao-recursive/everynoise1d.html'

def analyze_index():
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex for table rows (it's a massive table usually)
    # The structure saw earlier: [genre name](everynoise1d-GENRE.html) [☊](https://embed.spotify.com/?uri=spotify:playlist:ID)
    
    # Let's count genres by looking for links to everynoise1d-*.html
    genre_links = re.findall(r'href="everynoise1d-([^"]+)\.html">([^<]+)</a>', content)
    
    # Let's count playlists
    playlist_links = re.findall(r'spotify:playlist:([a-zA-Z0-9]+)', content)
    
    # Let's see if we can find colors
    # Often in <td style="color: #HEX">
    colors = re.findall(r'color:\s*(#[0-9a-fA-F]{6})', content)

    print(f"Total Content Length: {len(content):,} chars")
    print(f"Total Genres Found: {len(genre_links):,}")
    print(f"Total Playlists Found: {len(playlist_links):,}")
    print(f"Total Colors Found: {len(colors):,}")
    
    print("\n--- SAMPLE GENRES ---")
    for i in range(min(5, len(genre_links))):
        print(f"Genre: {genre_links[i][1]} (Slug: {genre_links[i][0]})")

    print("\n--- SAMPLE PLAYLISTS ---")
    for i in range(min(5, len(playlist_links))):
        print(f"Playlist ID: {playlist_links[i]}")

if __name__ == "__main__":
    analyze_index()
