#!/usr/bin/env python3
"""
Tycho-2 Star Catalog to SIF Converter
Converts the Tycho-2 catalog to Semantic Interchange Format (SIF)

Input: tyc2.dat.00 through tyc2.dat.19 (20 zone files, 2.5M stars total)
Output: tycho2_bright.sif.json (bright stars only, mag < 11)

Schema:
- Entities: Stars (with astrometric and photometric data)
- Relationships: Constellation membership (simplified)
"""

import json
import math
import gzip
from pathlib import Path
from typing import Dict, List
import sys

def parse_tycho_line(line: str) -> Dict:
    """Parse a single line from tyc2.dat"""
    try:
        # TYC identifier (columns 1-12)
        tyc1 = int(line[0:4].strip())
        tyc2 = int(line[5:10].strip())
        tyc3 = int(line[11:12].strip())
        
        # Position (J2000, degrees)
        ra_deg = float(line[15:27].strip())
        dec_deg = float(line[28:40].strip())
        
        # Proper motion (mas/yr)
        pm_ra = float(line[41:48].strip()) if line[41:48].strip() else 0.0
        pm_dec = float(line[49:56].strip()) if line[49:56].strip() else 0.0
        
        # Magnitudes (Tycho V_T and B_T)
        vt_mag = float(line[110:116].strip()) if line[110:116].strip() else 99.0
        bt_mag = float(line[123:129].strip()) if line[123:129].strip() else 99.0
        
        return {
            'tyc': f"{tyc1}-{tyc2}-{tyc3}",
            'ra': ra_deg,
            'dec': dec_deg,
            'pm_ra': pm_ra,
            'pm_dec': pm_dec,
            'vt_mag': vt_mag,
            'bt_mag': bt_mag
        }
    except (ValueError, IndexError) as e:
        return None

def calculate_importance(star: Dict) -> float:
    """Calculate importance score for a star"""
    importance = 0.5  # Base importance
    
    # Brighter stars are more important
    if star['vt_mag'] < 9.0:  # Very bright
        importance += 0.3
    if star['vt_mag'] < 6.0:  # Naked eye
        importance += 0.2
    
    # High proper motion (nearby/fast-moving stars)
    pm_total = math.sqrt(star['pm_ra']**2 + star['pm_dec']**2)
    if pm_total > 50:  # mas/yr
        importance += 0.1
    
    return min(importance, 1.0)

def convert_tycho_to_sif(input_dir: Path, output_file: Path, mag_limit: float = 11.0):
    """Convert Tycho-2 catalog to SIF format (bright stars only)"""
    print(f"📖 Reading Tycho-2 catalog from {input_dir}...")
    print(f"   Magnitude limit: V_T < {mag_limit}")
    
    entities = []
    total_processed = 0
    total_kept = 0
    
    # Process all 20 zone files
    for zone_num in range(20):
        zone_file = input_dir / f"tyc2.dat.{zone_num:02d}"
        
        # Check if file is gzipped or not
        if not zone_file.exists():
            zone_file = input_dir / f"tyc2.dat.{zone_num:02d}.gz"
            if zone_file.exists():
                print(f"  Extracting zone {zone_num:02d}...")
                import subprocess
                subprocess.run(['gunzip', '-k', str(zone_file)], check=True)
                zone_file = input_dir / f"tyc2.dat.{zone_num:02d}"
        
        if not zone_file.exists():
            print(f"  ⚠️  Zone {zone_num:02d} not found, skipping...")
            continue
        
        print(f"  Processing zone {zone_num:02d}...")
        
        with open(zone_file, 'r') as f:
            for line in f:
                total_processed += 1
                
                star = parse_tycho_line(line)
                if not star:
                    continue
                
                # Filter by magnitude
                if star['vt_mag'] >= mag_limit:
                    continue
                
                total_kept += 1
                
                # Create star entity
                attributes = {
                    'ra_deg': round(star['ra'], 6),
                    'dec_deg': round(star['dec'], 6),
                    'vt_magnitude': round(star['vt_mag'], 3),
                    'bt_magnitude': round(star['bt_mag'], 3),
                    'pm_ra_mas_yr': round(star['pm_ra'], 2),
                    'pm_dec_mas_yr': round(star['pm_dec'], 2),
                }
                
                # Calculate B-V color if both magnitudes available
                if star['bt_mag'] < 90 and star['vt_mag'] < 90:
                    bv_color = star['bt_mag'] - star['vt_mag']
                    attributes['bv_color'] = round(bv_color, 3)
                
                entity = {
                    'id': f"tyc_{star['tyc'].replace('-', '_')}",
                    'type': 'star',
                    'name': f"TYC {star['tyc']}",
                    'attributes': attributes,
                    'importance': calculate_importance(star)
                }
                entities.append(entity)
        
        print(f"    Zone {zone_num:02d}: {total_kept} bright stars (of {total_processed} total)")
    
    # Create SIF structure
    sif = {
        'version': '1.0',
        'metadata': {
            'title': 'Tycho-2 Bright Star Catalog',
            'description': f'Bright stars (V_T < {mag_limit}) from the Tycho-2 catalog (Høg et al. 2000)',
            'source': 'VizieR I/259',
            'created': '2026-01-09',
            'magnitude_limit': mag_limit,
            'total_processed': total_processed,
            'entity_count': len(entities),
            'relationship_count': 0
        },
        'entities': entities,
        'relationships': []
    }
    
    # Write SIF file
    print(f"\n💾 Writing {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(sif, f, indent=2)
    
    print(f"\n✅ Conversion complete!")
    print(f"   Total stars processed: {total_processed:,}")
    print(f"   Bright stars kept: {len(entities):,}")
    print(f"   Percentage: {100*len(entities)/total_processed:.1f}%")
    print(f"\n🌟 Very bright (V_T < 9): {sum(1 for e in entities if e['attributes']['vt_magnitude'] < 9.0):,}")
    print(f"👁️  Naked-eye (V_T < 6): {sum(1 for e in entities if e['attributes']['vt_magnitude'] < 6.0):,}")

if __name__ == '__main__':
    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('tycho2_bright.sif.json')
    mag_limit = float(sys.argv[3]) if len(sys.argv) > 3 else 11.0
    
    convert_tycho_to_sif(input_dir, output_file, mag_limit)
