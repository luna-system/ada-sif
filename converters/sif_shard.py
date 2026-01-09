#!/usr/bin/env python3
"""
SIF Sharding Script - Split large SIF files into smaller, linked shards
Implements SIF v1.1 "Linked SIFs" specification

For Hipparcos: Shard by constellation (20 shards)
For ENAO: Shard alphabetically (26 shards A-Z)
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

def shard_by_constellation(input_file: Path, output_dir: Path):
    """Shard Hipparcos catalog by constellation"""
    print(f"📖 Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Group entities and relationships by constellation
    constellation_shards = defaultdict(lambda: {'entities': [], 'relationships': []})
    constellation_entities = {}
    
    # First pass: collect constellation entities
    for entity in data['entities']:
        if entity['type'] == 'constellation':
            constellation_entities[entity['id']] = entity
    
    # Second pass: group stars by constellation
    for entity in data['entities']:
        if entity['type'] == 'star':
            # Find which constellation this star belongs to
            star_constellation = None
            for rel in data['relationships']:
                if rel['entity_a'] == entity['id'] and rel['relation_type'] == 'in_constellation':
                    star_constellation = rel['entity_b']
                    break
            
            if star_constellation:
                constellation_shards[star_constellation]['entities'].append(entity)
    
    # Third pass: add relationships
    for rel in data['relationships']:
        # Find which constellation this relationship belongs to
        constellation_id = rel['entity_b'] if rel['relation_type'] == 'in_constellation' else None
        if constellation_id:
            constellation_shards[constellation_id]['relationships'].append(rel)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write individual constellation shards
    shard_metadata = []
    for const_id, shard_data in constellation_shards.items():
        const_entity = constellation_entities[const_id]
        const_name = const_entity['name']
        
        # Add constellation entity to shard
        shard_data['entities'].insert(0, const_entity)
        
        # Create shard SIF
        shard_sif = {
            'version': '1.0',
            'metadata': {
                'title': f'Hipparcos Stars - {const_name}',
                'description': f'Stars in the constellation {const_name}',
                'shard_id': const_id,
                'entity_count': len(shard_data['entities']),
                'relationship_count': len(shard_data['relationships'])
            },
            'entities': shard_data['entities'],
            'relationships': shard_data['relationships']
        }
        
        # Write shard file
        shard_filename = f"{const_id}.sif.json"
        shard_path = output_dir / shard_filename
        with open(shard_path, 'w') as f:
            json.dump(shard_sif, f, indent=2)
        
        print(f"  ✅ {const_name}: {len(shard_data['entities'])} entities → {shard_filename}")
        
        # Track metadata
        shard_metadata.append({
            'id': const_id,
            'name': const_name,
            'url': shard_filename,
            'entity_count': len(shard_data['entities']),
            'relationship_count': len(shard_data['relationships'])
        })
    
    # Create master index (SIF v1.1 format)
    master_sif = {
        'version': '1.1',
        'metadata': {
            'title': 'Hipparcos Star Catalog (Sharded)',
            'description': 'Hipparcos-2 catalog split into constellation-based shards for progressive loading',
            'total_entities': data['metadata']['entity_count'],
            'total_relationships': data['metadata']['relationship_count'],
            'shard_count': len(shard_metadata),
            'shard_strategy': 'constellation'
        },
        'shards': shard_metadata
    }
    
    master_path = output_dir / 'hipparcos_shards.sif.json'
    with open(master_path, 'w') as f:
        json.dump(master_sif, f, indent=2)
    
    print(f"\n✅ Sharding complete!")
    print(f"   Master index: {master_path}")
    print(f"   Shards: {len(shard_metadata)}")
    print(f"   Total entities: {data['metadata']['entity_count']:,}")

def shard_alphabetically(input_file: Path, output_dir: Path):
    """Shard ENAO catalog alphabetically (A-Z)"""
    print(f"📖 Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Group entities by first letter
    letter_shards = defaultdict(lambda: {'entities': [], 'relationships': []})
    
    for entity in data['entities']:
        first_letter = entity['name'][0].upper()
        if first_letter.isalpha():
            letter_shards[first_letter]['entities'].append(entity)
        else:
            letter_shards['0-9']['entities'].append(entity)  # Numbers/symbols
    
    # Group relationships
    entity_to_shard = {}
    for letter, shard_data in letter_shards.items():
        for entity in shard_data['entities']:
            entity_to_shard[entity['id']] = letter
    
    for rel in data['relationships']:
        # Add relationship to shard of entity_a
        shard_letter = entity_to_shard.get(rel['entity_a'])
        if shard_letter:
            letter_shards[shard_letter]['relationships'].append(rel)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write individual letter shards
    shard_metadata = []
    for letter in sorted(letter_shards.keys()):
        shard_data = letter_shards[letter]
        
        # Create shard SIF
        shard_sif = {
            'version': '1.0',
            'metadata': {
                'title': f'ENAO Music - {letter}',
                'description': f'Genres and artists starting with {letter}',
                'shard_id': letter,
                'entity_count': len(shard_data['entities']),
                'relationship_count': len(shard_data['relationships'])
            },
            'entities': shard_data['entities'],
            'relationships': shard_data['relationships']
        }
        
        # Write shard file
        shard_filename = f"enao_{letter}.sif.json"
        shard_path = output_dir / shard_filename
        with open(shard_path, 'w') as f:
            json.dump(shard_sif, f, indent=2)
        
        print(f"  ✅ {letter}: {len(shard_data['entities'])} entities → {shard_filename}")
        
        # Track metadata
        shard_metadata.append({
            'id': letter,
            'name': f'Letter {letter}',
            'url': shard_filename,
            'entity_count': len(shard_data['entities']),
            'relationship_count': len(shard_data['relationships'])
        })
    
    # Create master index
    master_sif = {
        'version': '1.1',
        'metadata': {
            'title': 'ENAO Music Catalog (Sharded)',
            'description': 'Every Noise At Once catalog split alphabetically for progressive loading',
            'total_entities': data['metadata']['entity_count'] if 'metadata' in data else len(data['entities']),
            'total_relationships': data['metadata']['relationship_count'] if 'metadata' in data else len(data['relationships']),
            'shard_count': len(shard_metadata),
            'shard_strategy': 'alphabetical'
        },
        'shards': shard_metadata
    }
    
    master_path = output_dir / 'enao_shards.sif.json'
    with open(master_path, 'w') as f:
        json.dump(master_sif, f, indent=2)
    
    print(f"\n✅ Sharding complete!")
    print(f"   Master index: {master_path}")
    print(f"   Shards: {len(shard_metadata)}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python sif_shard.py <input.sif.json> <output_dir> <strategy>")
        print("Strategies: constellation, alphabetical")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    strategy = sys.argv[3]
    
    if strategy == 'constellation':
        shard_by_constellation(input_file, output_dir)
    elif strategy == 'alphabetical':
        shard_alphabetically(input_file, output_dir)
    else:
        print(f"Unknown strategy: {strategy}")
        sys.exit(1)
