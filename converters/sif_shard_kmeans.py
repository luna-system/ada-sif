#!/usr/bin/env python3
"""
ENAO K-Means Sharding - Use k-means clustering to find natural genre clusters
Creates balanced shards based on actual data distribution
"""

import json
import numpy as np
from pathlib import Path
from bs4 import BeautifulSoup
import re
from sklearn.cluster import KMeans
from collections import defaultdict

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

def shard_by_kmeans(sif_file: Path, positions_file: Path, output_dir: Path, n_clusters=16):
    """Shard SIF using k-means clustering on genre positions"""
    print(f"\n📊 Loading SIF from {sif_file}...")
    with open(sif_file, 'r') as f:
        sif_data = json.load(f)
    
    print(f"📍 Loading positions from {positions_file}...")
    genre_positions = extract_genre_positions(positions_file)
    
    # Prepare data for k-means
    genre_slugs = []
    positions = []
    
    for slug, pos in genre_positions.items():
        genre_slugs.append(slug)
        positions.append([pos['x'], pos['y']])
    
    positions = np.array(positions)
    
    print(f"\n🔬 Running k-means clustering (k={n_clusters})...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(positions)
    
    # Map genres to clusters
    genre_to_cluster = {}
    for slug, label in zip(genre_slugs, cluster_labels):
        genre_to_cluster[slug] = int(label)
    
    # Analyze cluster centers
    print(f"\n📊 Cluster centers:")
    for i, center in enumerate(kmeans.cluster_centers_):
        count = sum(1 for label in cluster_labels if label == i)
        print(f"  Cluster {i}: center=({center[0]:.0f}, {center[1]:.0f}), size={count}")
    
    # Create shards
    shards = defaultdict(lambda: {'entities': [], 'relationships': []})
    entity_to_shard = {}
    
    # Assign entities to shards
    for entity in sif_data['entities']:
        genre_slug = entity['id'].replace('genre_', '')
        
        if genre_slug in genre_to_cluster:
            cluster_id = genre_to_cluster[genre_slug]
            shard_id = f"cluster_{cluster_id}"
            shards[shard_id]['entities'].append(entity)
            entity_to_shard[entity['id']] = shard_id
        else:
            # Artists or unknown genres
            shards['artists']['entities'].append(entity)
            entity_to_shard[entity['id']] = 'artists'
    
    # Assign relationships to shards
    for rel in sif_data['relationships']:
        shard_id = entity_to_shard.get(rel['entity_a'], 'artists')
        shards[shard_id]['relationships'].append(rel)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write shard files
    shard_metadata = []
    
    for shard_id in sorted(shards.keys()):
        shard_data = shards[shard_id]
        
        if shard_id == 'artists':
            shard_name = "Artists Hub"
            shard_type = "hub"
        else:
            cluster_num = int(shard_id.split('_')[1])
            center = kmeans.cluster_centers_[cluster_num]
            
            # Describe cluster position
            x_desc = "Dense" if center[0] < 500 else "Mid" if center[0] < 1000 else "Bouncy"
            y_desc = "Organic" if center[1] < 5000 else "Mid-Organic" if center[1] < 11000 else "Mid-Electric" if center[1] < 17000 else "Electric"
            
            shard_name = f"{y_desc} + {x_desc} (Cluster {cluster_num})"
            shard_type = "module"
        
        # Create shard SIF
        shard_sif = {
            'version': '1.0',
            'metadata': {
                'title': f'ENAO Music - {shard_name}',
                'description': f'K-means cluster of genres in the music space',
                'shard_id': shard_id,
                'shard_type': shard_type,
                'entity_count': len(shard_data['entities']),
                'relationship_count': len(shard_data['relationships'])
            },
            'entities': shard_data['entities'],
            'relationships': shard_data['relationships']
        }
        
        # Write shard file
        shard_filename = f"enao_{shard_id}.sif.json"
        shard_path = output_dir / shard_filename
        with open(shard_path, 'w') as f:
            json.dump(shard_sif, f, indent=2)
        
        print(f"  ✅ {shard_name}: {len(shard_data['entities'])} entities → {shard_filename}")
        
        shard_metadata.append({
            'id': shard_id,
            'name': shard_name,
            'type': shard_type,
            'url': shard_filename,
            'entity_count': len(shard_data['entities']),
            'relationship_count': len(shard_data['relationships'])
        })
    
    # Create master index
    master_sif = {
        'version': '1.1',
        'metadata': {
            'title': 'ENAO Music Catalog (K-Means Sharded)',
            'description': f'Every Noise At Once catalog sharded using k-means clustering (k={n_clusters})',
            'total_entities': len(sif_data['entities']),
            'total_relationships': len(sif_data['relationships']),
            'shard_count': len(shard_metadata),
            'shard_strategy': 'kmeans',
            'n_clusters': n_clusters
        },
        'shards': shard_metadata
    }
    
    master_path = output_dir / 'enao_kmeans_shards.sif.json'
    with open(master_path, 'w') as f:
        json.dump(master_sif, f, indent=2)
    
    print(f"\n✅ K-means sharding complete!")
    print(f"   Master index: {master_path}")
    print(f"   Shards: {len(shard_metadata)}")
    
    # Print size distribution
    sizes = [s['entity_count'] for s in shard_metadata if s['type'] != 'hub']
    print(f"\n📊 Cluster size distribution:")
    print(f"   Min: {min(sizes)}")
    print(f"   Max: {max(sizes)}")
    print(f"   Mean: {sum(sizes)/len(sizes):.0f}")
    print(f"   Std: {np.std(sizes):.0f}")

if __name__ == '__main__':
    import sys
    
    sif_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('enao_maximalist.sif.json')
    positions_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('engenremap.html')
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('kmeans_shards')
    n_clusters = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    
    shard_by_kmeans(sif_file, positions_file, output_dir, n_clusters)
