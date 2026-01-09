#!/usr/bin/env python3
"""
Hipparcos-2 Star Catalog to SIF Converter
Converts the Hipparcos-2 astrometric catalog to Semantic Interchange Format (SIF)

Input: hip2.dat (Hipparcos-2 catalog, 117,955 stars)
Output: hipparcos_stars.sif.json

Schema:
- Entities: Stars (with astrometric and photometric data)
- Relationships: Constellation membership, proximity clusters
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Constellation boundaries (simplified - using RA/Dec ranges)
# This is a simplified mapping - real constellation boundaries are complex polygons
CONSTELLATIONS = {
    'Andromeda': {'ra_min': 0, 'ra_max': 50, 'dec_min': 20, 'dec_max': 50},
    'Aquarius': {'ra_min': 310, 'ra_max': 350, 'dec_min': -25, 'dec_max': 5},
    'Aquila': {'ra_min': 280, 'ra_max': 310, 'dec_min': -10, 'dec_max': 20},
    'Aries': {'ra_min': 20, 'ra_max': 50, 'dec_min': 10, 'dec_max': 30},
    'Cancer': {'ra_min': 110, 'ra_max': 140, 'dec_min': 5, 'dec_max': 35},
    'Canis Major': {'ra_min': 95, 'ra_max': 115, 'dec_min': -35, 'dec_max': -10},
    'Capricornus': {'ra_min': 300, 'ra_max': 330, 'dec_min': -30, 'dec_max': -5},
    'Cassiopeia': {'ra_min': 350, 'ra_max': 30, 'dec_min': 50, 'dec_max': 70},
    'Cygnus': {'ra_min': 290, 'ra_max': 320, 'dec_min': 25, 'dec_max': 60},
    'Gemini': {'ra_min': 85, 'ra_max': 120, 'dec_min': 10, 'dec_max': 35},
    'Leo': {'ra_min': 140, 'ra_max': 180, 'dec_min': 0, 'dec_max': 30},
    'Lyra': {'ra_min': 270, 'ra_max': 295, 'dec_min': 25, 'dec_max': 50},
    'Orion': {'ra_min': 70, 'ra_max': 95, 'dec_min': -10, 'dec_max': 20},
    'Pegasus': {'ra_min': 320, 'ra_max': 10, 'dec_min': 5, 'dec_max': 35},
    'Perseus': {'ra_min': 30, 'ra_max': 60, 'dec_min': 30, 'dec_max': 60},
    'Sagittarius': {'ra_min': 270, 'ra_max': 300, 'dec_min': -45, 'dec_max': -15},
    'Scorpius': {'ra_min': 235, 'ra_max': 265, 'dec_min': -45, 'dec_max': -10},
    'Taurus': {'ra_min': 50, 'ra_max': 90, 'dec_min': 0, 'dec_max': 30},
    'Ursa Major': {'ra_min': 120, 'ra_max': 220, 'dec_min': 40, 'dec_max': 70},
    'Virgo': {'ra_min': 170, 'ra_max': 220, 'dec_min': -20, 'dec_max': 15},
}

def parse_hipparcos_line(line: str) -> Dict:
    """Parse a single line from hip2.dat"""
    try:
        hip = int(line[0:6].strip())
        ra_rad = float(line[15:28].strip())
        dec_rad = float(line[29:42].strip())
        parallax = float(line[43:50].strip()) if line[43:50].strip() else 0.0
        pm_ra = float(line[51:59].strip()) if line[51:59].strip() else 0.0
        pm_dec = float(line[60:68].strip()) if line[60:68].strip() else 0.0
        hpmag = float(line[129:136].strip()) if line[129:136].strip() else 99.0
        bv_color = float(line[152:158].strip()) if line[152:158].strip() and line[152:158].strip() != '' else None
        
        # Convert RA/Dec from radians to degrees
        ra_deg = math.degrees(ra_rad)
        dec_deg = math.degrees(dec_rad)
        
        # Calculate distance from parallax (in parsecs)
        distance_pc = (1000.0 / parallax) if parallax > 0 else None
        
        return {
            'hip': hip,
            'ra': ra_deg,
            'dec': dec_deg,
            'parallax': parallax,
            'distance_pc': distance_pc,
            'pm_ra': pm_ra,
            'pm_dec': pm_dec,
            'magnitude': hpmag,
            'bv_color': bv_color
        }
    except (ValueError, IndexError) as e:
        return None

def get_constellation(ra_deg: float, dec_deg: float) -> str:
    """Determine constellation based on RA/Dec (simplified)"""
    for const_name, bounds in CONSTELLATIONS.items():
        ra_min, ra_max = bounds['ra_min'], bounds['ra_max']
        dec_min, dec_max = bounds['dec_min'], bounds['dec_max']
        
        # Handle RA wrap-around at 0/360
        if ra_max < ra_min:  # Wraps around 0
            if (ra_deg >= ra_min or ra_deg <= ra_max) and dec_min <= dec_deg <= dec_max:
                return const_name
        else:
            if ra_min <= ra_deg <= ra_max and dec_min <= dec_deg <= dec_max:
                return const_name
    
    return 'Unknown'

def calculate_importance(star: Dict) -> float:
    """Calculate importance score for a star"""
    importance = 0.5  # Base importance
    
    # Brighter stars are more important
    if star['magnitude'] < 6.0:  # Visible to naked eye
        importance += 0.3
    if star['magnitude'] < 3.0:  # Bright star
        importance += 0.2
    
    # Closer stars are more important
    if star['distance_pc'] and star['distance_pc'] < 100:
        importance += 0.2
    if star['distance_pc'] and star['distance_pc'] < 25:
        importance += 0.1
    
    # High proper motion (nearby/fast-moving stars)
    pm_total = math.sqrt(star['pm_ra']**2 + star['pm_dec']**2)
    if pm_total > 100:  # mas/yr
        importance += 0.1
    
    return min(importance, 1.0)

def convert_hipparcos_to_sif(input_file: Path, output_file: Path, max_stars: int = None):
    """Convert Hipparcos catalog to SIF format"""
    print(f"📖 Reading {input_file}...")
    
    entities = []
    relationships = []
    constellation_counts = {}
    
    with open(input_file, 'r') as f:
        for i, line in enumerate(f):
            if max_stars and i >= max_stars:
                break
            
            star = parse_hipparcos_line(line)
            if not star:
                continue
            
            # Determine constellation
            constellation = get_constellation(star['ra'], star['dec'])
            constellation_counts[constellation] = constellation_counts.get(constellation, 0) + 1
            
            # Create star entity
            attributes = {
                'ra_deg': round(star['ra'], 6),
                'dec_deg': round(star['dec'], 6),
                'parallax_mas': round(star['parallax'], 2),
                'magnitude': round(star['magnitude'], 2),
                'pm_ra_mas_yr': round(star['pm_ra'], 2),
                'pm_dec_mas_yr': round(star['pm_dec'], 2),
            }
            
            if star['distance_pc']:
                attributes['distance_pc'] = round(star['distance_pc'], 1)
                attributes['distance_ly'] = round(star['distance_pc'] * 3.26156, 1)
            
            if star['bv_color'] is not None:
                attributes['bv_color'] = round(star['bv_color'], 3)
            
            entity = {
                'id': f"hip_{star['hip']}",
                'type': 'star',
                'name': f"HIP {star['hip']}",
                'attributes': attributes,
                'importance': calculate_importance(star)
            }
            entities.append(entity)
            
            # Create constellation relationship
            if constellation != 'Unknown':
                relationships.append({
                    'entity_a': f"hip_{star['hip']}",
                    'relation_type': 'in_constellation',
                    'entity_b': f"constellation_{constellation.lower().replace(' ', '_')}",
                    'strength': 1.0
                })
            
            if (i + 1) % 10000 == 0:
                print(f"  Processed {i + 1} stars...")
    
    # Create constellation entities
    for const_name, count in constellation_counts.items():
        if const_name != 'Unknown':
            entities.append({
                'id': f"constellation_{const_name.lower().replace(' ', '_')}",
                'type': 'constellation',
                'name': const_name,
                'attributes': {
                    'star_count': count
                },
                'importance': 0.7
            })
    
    # Create SIF structure
    sif = {
        'version': '1.0',
        'metadata': {
            'title': 'Hipparcos-2 Star Catalog',
            'description': 'Astrometric catalog of 117,955 stars from the Hipparcos space mission (van Leeuwen 2007 reduction)',
            'source': 'VizieR I/311',
            'created': '2026-01-09',
            'entity_count': len(entities),
            'relationship_count': len(relationships)
        },
        'entities': entities,
        'relationships': relationships
    }
    
    # Write SIF file
    print(f"\n💾 Writing {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(sif, f, indent=2)
    
    print(f"\n✅ Conversion complete!")
    print(f"   Entities: {len(entities):,}")
    print(f"   Relationships: {len(relationships):,}")
    print(f"   Constellations: {len(constellation_counts)}")
    print(f"\n🌟 Brightest stars (mag < 3.0): {sum(1 for e in entities if e['type'] == 'star' and e['attributes']['magnitude'] < 3.0)}")
    print(f"👁️  Naked-eye visible (mag < 6.0): {sum(1 for e in entities if e['type'] == 'star' and e['attributes']['magnitude'] < 6.0)}")

if __name__ == '__main__':
    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('hip2.dat')
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('hipparcos_stars.sif.json')
    max_stars = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    convert_hipparcos_to_sif(input_file, output_file, max_stars)
