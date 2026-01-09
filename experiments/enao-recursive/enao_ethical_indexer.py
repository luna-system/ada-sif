#!/usr/bin/env python3
"""
Every Noise At Once - Ethical Indexer
=====================================

Parses the locally downloaded `everynoise1d.html` to extract the full genre index
without crawling the website.

Extracts:
- Genre Name
- Genre Slug (for MusicBrainz/URL matching)
- Spotify Playlist ID (for reference/hydration)
- Color Hex Code (preserves the visual map data!)

Output:
- enao_genre_index.json
"""

import re
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup  # Robust parsing

INDEX_FILE = Path('everynoise1d.html')
OUTPUT_FILE = Path('enao_genre_index.json')

def parse_index():
    print(f"📖 Reading {INDEX_FILE}...")
    
    if not INDEX_FILE.exists():
        print(f"❌ Error: {INDEX_FILE} not found. Please download it first.")
        sys.exit(1)

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    genres = []
    
    # The data is in a massive table
    # Rows look like:
    # <tr>
    #   <td>Rank</td>
    #   <td><a href="spotify:playlist:ID">PLAY</a></td>
    #   <td><a href="everynoise1d-slug.html" style="color: #HEX">Name</a></td>
    # </tr>
    
    rows = soup.find_all('tr')
    print(f"🔍 Found {len(rows):,} rows. Parsing...")

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        # Cell 1: Playlist Link
        playlist_link = cells[1].find('a')
        if not playlist_link:
            continue
            
        href = playlist_link.get('href', '')
        # Format: https://embed.spotify.com/?uri=spotify:playlist:ID
        match = re.search(r'spotify:playlist:([a-zA-Z0-9]+)', href)
        if not match:
            continue
        playlist_id = match.group(1)

        # Cell 2: Genre Link & Name
        genre_link = cells[2].find('a')
        if not genre_link:
            continue
            
        name = genre_link.get_text().strip()
        genre_href = genre_link.get('href', '')
        # Format: everynoise1d-slug.html
        slug_match = re.search(r'everynoise1d-([^"]+)\.html', genre_href)
        slug = slug_match.group(1) if slug_match else name.lower().replace(' ', '')
        
        # Color style
        style = genre_link.get('style', '')
        color_match = re.search(r'color:\s*(#[0-9a-fA-F]{6})', style)
        color = color_match.group(1) if color_match else "#888888"

        genres.append({
            'name': name,
            'slug': slug,
            'playlist_id': playlist_id,
            'color': color
        })

    print(f"✅ Extracted {len(genres):,} genres!")
    
    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(genres, f, indent=2, ensure_ascii=False)
        
    print(f"💾 Saved index to {OUTPUT_FILE}")
    
    # Preview
    print("\n--- First 5 Genres ---")
    for g in genres[:5]:
        print(f"{g['name']} ({g['color']}) -> {g['playlist_id']}")

if __name__ == "__main__":
    parse_index()
