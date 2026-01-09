#!/usr/bin/env python3
"""
ENAO Spatial Sharding - Shard by X/Y position on the genre scatter plot
Uses Glenn McDonald's Every Noise At Once spatial layout:
- X-axis: Dense/Atmospheric (left) ← → Spiky/Bouncy (right)
- Y-axis: Organic (down) ← → Mechanical/Electric (up)

Creates 16 shards (4x4 grid) based on spatial position
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

def extract_genre_positions(html_file: Path):
    """Extract genre names and X/Y positions from engenremap.html"""
    print(f"📖 Parsing {html_file}...")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    genre_positions = {}
    
    # Find all genre divs with style containing top/left
    for div in soup.find_all('div', style=True):
        style = div.get('style', '')
        
        # Extract top and left positions
        top_match = re.search(r'top:\s*(\d+)px', style)
        left_match = re.search(r'left:\s*(\d+)px', style)
        
        if top_match and left_match:
            top = int(top_match.group(1))
            left = int(left_match.group(1))
            
            # Get genre name from the div content or link
            genre_link = div.find('a')
            if genre_link:
                # Extract genre slug from the link
                href = genre_link.get('href', '')
                if 'engenremap-' in href:
                    genre_slug = href.replace('engenremap-', '').replace('.html', '')
                    genre_positions[genre_slug] = {'x': left, 'y': top}
    
    print(f"  Found {len(genre_positions)} genres with positions")
    return genre_positions

def assign_to_quadrant(x, y, x_min, x_max, y_min, y_max, grid_size=4):
    """Assign a position to a quadrant in a grid"""
    # Normalize to 0-1
    x_norm = (x - x_min) / (x_max - x_min) if x_max > x_min else 0.5
    y_norm = (y - y_min) / (y_max - y_min) if y_max > y_min else 0.5
    
    # Determine grid cell (0 to grid_size-1)
    x_cell = min(int(x_norm * grid_size), grid_size - 1)
    y_cell = min(int(y_norm * grid_size), grid_size - 1)
    
    return (x_cell, y_cell)

def shard_by_spatial_position(sif_file: Path, positions_file: Path, output_dir: Path, grid_size=4):
    """Shard SIF by spatial position on ENAO scatter plot"""
    print(f"\n📊 Loading SIF from {sif_file}...")
    with open(sif_file, 'r') as f:
        sif_data = json.load(f)
    
    print(f"📍 Loading positions from {positions_file}...")
    genre_positions = extract_genre_positions(positions_file)
    
    # Find bounds
    x_values = [p['x'] for p in genre_positions.values()]
    y_values = [p['y'] for p in genre_positions.values()]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    
    print(f"  X range: {x_min} - {x_max}")
    print(f"  Y range: {y_min} - {y_max}")
    
    # Create shards
    shards = defaultdict(lambda: {'entities': [], 'relationships': []})
    entity_to_shard = {}
    
    # Assign entities to shards
    for entity in sif_data['entities']:
        # Try to find position for this genre
        genre_slug = entity['id'].replace('genre_', '')
        
        if genre_slug in genre_positions:
            pos = genre_positions[genre_slug]
            quadrant = assign_to_quadrant(pos['x'], pos['y'], x_min, x_max, y_min, y_max, grid_size)
            shard_id = f"q{quadrant[0]}{quadrant[1]}"
            shards[shard_id]['entities'].append(entity)
            entity_to_shard[entity['id']] = shard_id
        else:
            # If no position found, put in a default "unknown" shard
            shards['unknown']['entities'].append(entity)
            entity_to_shard[entity['id']] = 'unknown'
    
    # Assign relationships to shards
    for rel in sif_data['relationships']:
        shard_id = entity_to_shard.get(rel['entity_a'], 'unknown')
        shards[shard_id]['relationships'].append(rel)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write shard files
    shard_metadata = []
    for shard_id in sorted(shards.keys()):
        shard_data = shards[shard_id]
        
        # Parse quadrant coordinates
        if shard_id != 'unknown':
            x_cell = int(shard_id[1])
            y_cell = int(shard_id[2])
            
            # Describe the quadrant
            x_desc = ['Dense/Atmospheric', 'Mid-Atmospheric', 'Mid-Bouncy', 'Spiky/Bouncy'][x_cell]
            y_desc = ['Organic', 'Mid-Organic', 'Mid-Electric', 'Mechanical/Electric'][y_cell]
            shard_name = f"{y_desc} + {x_desc}"
        else:
            shard_name = "Unknown Position"
        
        # Create shard SIF
        shard_sif = {
            'version': '1.0',
            'metadata': {
                'title': f'ENAO Music - {shard_name}',
                'description': f'Genres in the {shard_name} region of the music space',
                'shard_id': shard_id,
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
            'url': shard_filename,
            'entity_count': len(shard_data['entities']),
            'relationship_count': len(shard_data['relationships'])
        })
    
    # Create master index
    master_sif = {
        'version': '1.1',
        'metadata': {
            'title': 'ENAO Music Catalog (Spatially Sharded)',
            'description': 'Every Noise At Once catalog sharded by position on the genre scatter plot (4x4 grid)',
            'total_entities': len(sif_data['entities']),
            'total_relationships': len(sif_data['relationships']),
            'shard_count': len(shard_metadata),
            'shard_strategy': 'spatial_4x4',
            'axes': {
                'x': 'Dense/Atmospheric (left) ← → Spiky/Bouncy (right)',
                'y': 'Organic (down) ← → Mechanical/Electric (up)'
            }
        },
        'shards': shard_metadata
    }
    
    master_path = output_dir / 'enao_spatial_shards.sif.json'
    with open(master_path, 'w') as f:
        json.dump(master_sif, f, indent=2)
    
    print(f"\n✅ Spatial sharding complete!")
    print(f"   Master index: {master_path}")
    print(f"   Shards: {len(shard_metadata)}")

if __name__ == '__main__':
    import sys
    
    sif_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('enao_maximalist.sif.json')
    positions_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('engenremap.html')
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('spatial_shards')
    
    shard_by_spatial_position(sif_file, positions_file, output_dir)
