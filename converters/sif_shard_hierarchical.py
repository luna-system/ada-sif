#!/usr/bin/env python3
"""
ENAO Hierarchical Sharding - Create genre clusters + artist hub with top-N duplicates
Uses k-means clustering + hub-and-spoke model for scalable music exploration
"""

import json
import numpy as np
from pathlib import Path
from bs4 import BeautifulSoup
import re
from sklearn.cluster import KMeans
from collections import defaultdict, Counter

def extract_genre_positions(html_file: Path):
    """Extract genre names and X/Y positions from engenremap.html"""
    print(f"📖 Parsing {html_file}...")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    genre_positions = {}
    
    for div in soup.find_all('div', style=True):
        style = div.get('style', '')
        
        top_match = re.search(r'top:\s*(\d+)px', style)
        left_match = re.search(r'left:\s*(\d+)px', style)
        
        if top_match and left_match:
            top = int(top_match.group(1))
            left = int(left_match.group(1))
            
            genre_link = div.find('a')
            if genre_link:
                href = genre_link.get('href', '')
                if 'engenremap-' in href:
                    genre_slug = href.replace('engenremap-', '').replace('.html', '')
                    genre_positions[genre_slug] = {'x': left, 'y': top}
    
    print(f"  Found {len(genre_positions)} genres with positions")
    return genre_positions

def create_hierarchical_shards(sif_file: Path, positions_file: Path, output_dir: Path, 
                               n_clusters=16, top_n_artists=10):
    """Create hierarchical shards: genre clusters + artist hub"""
    print(f"\n📊 Loading SIF from {sif_file}...")
    with open(sif_file, 'r') as f:
        sif_data = json.load(f)
    
    print(f"📍 Loading positions from {positions_file}...")
    genre_positions = extract_genre_positions(positions_file)
    
    # Run k-means clustering
    genre_slugs = []
    positions = []
    
    for slug, pos in genre_positions.items():
        genre_slugs.append(slug)
        positions.append([pos['x'], pos['y']])
    
    positions = np.array(positions)
    
    print(f"\n🔬 Running k-means clustering (k={n_clusters})...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(positions)
    
    genre_to_cluster = {}
    for slug, label in zip(genre_slugs, cluster_labels):
        genre_to_cluster[slug] = int(label)
    
    # Separate genres and artists
    genres = []
    artists = []
    genre_artist_map = defaultdict(list)  # genre_id -> [artist_ids]
    
    for entity in sif_data['entities']:
        if entity['type'] == 'genre':
            genres.append(entity)
        elif entity['type'] == 'artist':
            artists.append(entity)
    
    # Build genre-artist relationships
    for rel in sif_data['relationships']:
        if rel['relation_type'] == 'has_artist':
            genre_artist_map[rel['entity_a']].append(rel['entity_b'])
    
    # Create artist hub (canonical source)
    # Create genre cluster shards (Distributed Holographic Model)
    # Each cluster contains its genres and ALL associated artists (duplicated across clusters)
    print(f"\n📦 Creating genre cluster shards (Distributed Holographic Model)...")
    
    cluster_shards = defaultdict(lambda: {'genres': [], 'artists': set(), 'relationships': []})
    artist_lookup = {a['id']: a for a in artists}
    shard_metadata = []
    
    # Assign genres to clusters
    for genre in genres:
        genre_slug = genre['id'].replace('genre_', '')
        
        if genre_slug in genre_to_cluster:
            cluster_id = genre_to_cluster[genre_slug]
            cluster_shards[cluster_id]['genres'].append(genre)
            
            # Get ALL artists for this genre (Distributed/Holographic)
            genre_artists = genre_artist_map.get(genre['id'], [])
            for artist_id in genre_artists:
                cluster_shards[cluster_id]['artists'].add(artist_id)
    
    # Build cluster shard files
    for cluster_id in sorted(cluster_shards.keys()):
        shard_data = cluster_shards[cluster_id]
        center = kmeans.cluster_centers_[cluster_id]
        
        # Describe cluster position
        x_desc = "Dense" if center[0] < 500 else "Mid" if center[0] < 1000 else "Bouncy"
        y_desc = "Organic" if center[1] < 5000 else "Mid-Organic" if center[1] < 11000 else "Mid-Electric" if center[1] < 17000 else "Electric"
        shard_name = f"{y_desc} + {x_desc}"
        
        # Collect entities (genres + ALL artists)
        entities = shard_data['genres'].copy()
        for artist_id in shard_data['artists']:
            if artist_id in artist_lookup:
                artist = artist_lookup[artist_id].copy()
                # No duplicate_of: Every shard holds the full holographic truth of the artist
                entities.append(artist)
        
        # Collect relationships (local within the holographic shard)
        relationships = []
        entity_ids = {e['id'] for e in entities}
        
        for rel in sif_data['relationships']:
            if rel['entity_a'] in entity_ids and rel['entity_b'] in entity_ids:
                rel_copy = rel.copy()
                rel_copy['scope'] = 'local'
                relationships.append(rel_copy)
        
        # Create shard
        shard_sif = {
            'version': '1.1',
            'metadata': {
                'title': f'ENAO Music - {shard_name}',
                'description': f'Genre cluster with full artist distribution',
                'shard_id': f'cluster_{cluster_id}',
                'shard_type': 'branch', # Updated from module
                'entity_count': len(entities),
                'relationship_count': len(relationships),
                'genre_count': len(shard_data['genres']),
                'artist_count': len(shard_data['artists'])
            },
            'entities': entities,
            'relationships': relationships
        }
        
        shard_filename = f"enao_cluster_{cluster_id}.sif.json"
        shard_path = output_dir / shard_filename
        with open(shard_path, 'w') as f:
            json.dump(shard_sif, f, indent=2)
        
        print(f"  ✅ {shard_name}: {len(shard_data['genres'])} genres, {len(shard_data['artists'])} artists → {shard_filename}")
        
        shard_metadata.append({
            'id': f'cluster_{cluster_id}',
            'name': shard_name,
            'type': 'branch',
            'url': shard_filename,
            'entity_count': len(entities),
            'relationship_count': len(relationships)
        })
    
    # Create master index
    master_sif = {
        'version': '1.1',
        'metadata': {
            'title': 'ENAO Music Catalog (Holographic)',
            'description': f'K-means clustered genres with distributed artist holograms',
            'total_entities': len(sif_data['entities']),
            'total_relationships': len(sif_data['relationships']),
            'shard_count': len(shard_metadata),
            'shard_strategy': 'holographic_kmeans',
            'n_clusters': n_clusters
        },
        'shards': shard_metadata
    }
    
    master_path = output_dir / 'enao_hierarchical_shards.sif.json'
    with open(master_path, 'w') as f:
        json.dump(master_sif, f, indent=2)
    
    print(f"\n✅ Holographic sharding complete!")
    print(f"   Master index: {master_path}")
    print(f"   Genre clusters: {n_clusters}")
    print(f"   Total shards: {len(shard_metadata)}")

if __name__ == '__main__':
    import sys
    
    sif_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('enao_maximalist.sif.json')
    positions_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('engenremap.html')
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('hierarchical_shards')
    n_clusters = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    top_n = int(sys.argv[5]) if len(sys.argv) > 5 else 10
    
    create_hierarchical_shards(sif_file, positions_file, output_dir, n_clusters, top_n)
