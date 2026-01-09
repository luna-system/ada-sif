#!/usr/bin/env python3
"""
MusicBrainz Graph Hydrator (Maximalist Edition)
===============================================

Hydrates the Every Noise At Once (ENAO) genre index with semantic data from MusicBrainz.

Features:
- **Maximalist:** Fetches Top 50 Artists per Genre.
- **Robust:** Saves checkpoints every 50 genres.
- **Polite:** Respects MBz rate limits with exponential backoff.
- **Linked:** Metadata prepared for future SIF v1.1 linking.

Usage:
  python mbz_graph_hydrator.py [limit_genres]

"""

import json
import time
import requests
import sys
import os
from pathlib import Path
from datetime import datetime

# Config
INDEX_FILE = Path('enao_genre_index.json')
OUTPUT_SIF = Path('enao_maximalist.sif.json')
CHECKPOINT_FILE = Path('enao_checkpoint.json')
USER_AGENT = "Ada-SIF/1.0 ( ada@airsi.de )"
MBZ_API_ROOT = "https://musicbrainz.org/ws/2"
ARTIST_LIMIT = 50  # Ishkur-level depth!
CHECKPOINT_INTERVAL = 50

def get_artists_by_tag(tag, limit=50, retries=3):
    """Query MBz for artists with a specific tag."""
    url = f"{MBZ_API_ROOT}/artist"
    params = {
        'query': f'tag:"{tag}"',
        'fmt': 'json',
        'limit': limit
    }
    headers = {'User-Agent': USER_AGENT}
    
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                # Polite sleep on success
                time.sleep(1.1)
                data = response.json()
                return data.get('artists', [])
            
            elif response.status_code == 503:
                wait_time = (attempt + 1) * 2
                print(f"⚠️ Rate limited (503). Sleeping {wait_time}s...", flush=True)
                time.sleep(wait_time)
                continue
            
            elif response.status_code == 404:
                 return []
                 
            else:
                print(f"❌ Error {response.status_code} for tag '{tag}'", flush=True)
                return []
                
        except Exception as e:
            print(f"❌ Exception for tag '{tag}': {e}", flush=True)
            time.sleep(1)
            
    return []

def save_checkpoint(entities, relationships, processed_indices):
    """Save partial progress to disk."""
    data = {
        'entities': entities,
        'relationships': relationships,
        'processed_indices': list(processed_indices)
    }
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"💾 Checkpoint saved ({len(entities)} entities)", flush=True)

def load_checkpoint():
    """Load progress if exists."""
    if CHECKPOINT_FILE.exists():
        print("📂 Loading checkpoint...", flush=True)
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['entities'], data['relationships'], set(data['processed_indices'])
    return [], [], set()

def hydrate_graph(sample_limit=None):
    print(f"📖 Loading index from {INDEX_FILE}...")
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        genres = json.load(f)
        
    if sample_limit:
        genres = genres[:sample_limit]
        print(f"🔬 Sample Mode: Processing first {sample_limit} genres.")

    # Load checkpoint or init
    entities, relationships, processed_indices = load_checkpoint()
    
    # Track existing IDs to avoid duplicates in memory
    existing_ids = {e['id'] for e in entities}
    
    # We need to filter relationships to avoid dupes too
    # Simple set of "A->B" strings
    existing_rels = {f"{r['entity_a']}->{r['entity_b']}" for r in relationships}

    print(f"🌊 Hydrating with Top {ARTIST_LIMIT} Artists per Genre...", flush=True)
    
    start_time = time.time()
    
    for i, genre in enumerate(genres):
        if i in processed_indices:
            continue
            
        name = genre['name']
        slug = genre['slug']
        color = genre['color']
        
        # Polite logging
        elapsed = time.time() - start_time
        processed_count = len(processed_indices) + 1 # +1 for current
        avg_time = elapsed / processed_count if processed_count > 0 else 0
        remaining = len(genres) - processed_count
        est_hours = (remaining * 1.2) / 3600 # rough estimate
        
        print(f"[{i+1}/{len(genres)}] '{name}' (Est: {est_hours:.1f}h left)...", end='', flush=True)
        
        # 1. Add Genre Entity (if not exists)
        genre_id = f"genre_{slug}"
        if genre_id not in existing_ids:
            entities.append({
                'id': genre_id,
                'type': 'genre',
                'name': name,
                'description': f"Musical genre: {name}",
                'importance': 0.8,
                'attributes': {
                    'color': color,
                    'playlist_id': genre['playlist_id'],
                    'source': 'Every Noise At Once'
                }
            })
            existing_ids.add(genre_id)
        
        # 2. Query MusicBrainz
        artists = get_artists_by_tag(name, limit=ARTIST_LIMIT)
        
        if artists:
            print(f" Found {len(artists)}.", flush=True)
            
            for artist in artists:
                artist_name = artist['name']
                mbid = artist['id']
                artist_id = f"artist_{mbid}"
                
                # Add Artist Entity
                if artist_id not in existing_ids:
                    entities.append({
                        'id': artist_id,
                        'type': 'artist',
                        'name': artist_name,
                        'description': f"Artist: {artist_name}",
                        'importance': 0.9,
                        'attributes': {
                            'mbid': mbid,
                            'country': artist.get('country', 'Unknown'),
                            'type': artist.get('type', 'Unknown')
                        }
                    })
                    existing_ids.add(artist_id)
                
                # Add Relationship (Genre -> Artist)
                # This explicitly links the Genre node to the Artist node
                rel_key = f"{genre_id}->{artist_id}"
                if rel_key not in existing_rels:
                    relationships.append({
                        'entity_a': genre_id,
                        'relation_type': 'has_artist',
                        'entity_b': artist_id,
                        'strength': 1.0
                    })
                    existing_rels.add(rel_key)
        else:
            print(" No artists.", flush=True)

        processed_indices.add(i)
        
        # Checkpoint
        if len(processed_indices) % CHECKPOINT_INTERVAL == 0:
            save_checkpoint(entities, relationships, processed_indices)

    # Final Save
    save_checkpoint(entities, relationships, processed_indices) # Save final state to CP just in case
    
    # Build SIF
    sif = {
        'metadata': {
            'version': '1.0.0', # v1.1 features implicitly supported via attributes
            'timestamp': datetime.now().isoformat() + 'Z',
            'domain': 'music',
            'source': 'Every Noise Index + MusicBrainz API',
            'stats': {
                'genres': len(genres),
                'entities': len(entities),
                'relationships': len(relationships)
            }
        },
        'summary': {
            'text': f"A maximalist semantic graph of {len(genres)} genres and {len(entities)-len(genres)} artists from MusicBrainz.",
        },
        'entities': entities,
        'relationships': relationships
    }
    
    outfile = OUTPUT_SIF
    if sample_limit:
        outfile = Path(f'enao_maximalist_sample_{sample_limit}.sif.json')
        
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(sif, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Maximalist Hydration Complete!")
    print(f"Entities: {len(entities):,}")
    print(f"Relationships: {len(relationships):,}")
    print(f"Saved to {outfile}")

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    hydrate_graph(sample_limit=limit)
