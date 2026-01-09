#!/usr/bin/env python3
"""
Embed SIF data into HTML viewer
================================

Creates a standalone HTML file with SIF data embedded.

Usage:
    python embed_sif_viewer.py --input ishkurs_guide.sif.json --output ishkurs_viewer.html
"""

import json
from pathlib import Path
import argparse


def embed_sif_in_html(sif_path: Path, html_template: Path, output_path: Path):
    """Embed SIF JSON into HTML viewer template."""
    
    print(f"📄 Embedding {sif_path} into HTML viewer...")
    
    # Load SIF
    with open(sif_path, 'r', encoding='utf-8') as f:
        sif_data = json.load(f)
    
    # Load HTML template
    with open(html_template, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Embed SIF data - replace the entire line
    sif_json = json.dumps(sif_data, ensure_ascii=False)
    html = html.replace('const SIF_DATA = null; // Replace with actual SIF JSON', f'const SIF_DATA = {sif_json};')
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    file_size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"✅ Created {output_path} ({file_size_mb:.1f} MB)")
    print(f"   Open in browser to view {len(sif_data['entities']):,} entities!")


def main():
    parser = argparse.ArgumentParser(description='Embed SIF data into HTML viewer')
    parser.add_argument('--input', type=Path, required=True, help='Input SIF file')
    parser.add_argument('--template', type=Path, default=Path('sif_viewer.html'), help='HTML template')
    parser.add_argument('--output', type=Path, required=True, help='Output HTML file')
    
    args = parser.parse_args()
    
    embed_sif_in_html(args.input, args.template, args.output)


if __name__ == '__main__':
    main()
