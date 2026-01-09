#!/usr/bin/env python3
"""
SIF → Gephi Converter
=====================

Converts SIF format back to Gephi GEXF format for visualization and comparison.

Usage:
    python sif_to_gephi.py --input ishkurs_guide.sif.json --output ishkurs_from_sif.gexf
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
import argparse
from datetime import datetime


def sif_to_gexf(sif: dict) -> str:
    """Convert SIF document to GEXF (Gephi Exchange Format)."""
    
    # Create root GEXF element
    gexf = ET.Element('gexf', {
        'xmlns': 'http://www.gexf.net/1.2draft',
        'version': '1.2'
    })
    
    # Add metadata
    meta = ET.SubElement(gexf, 'meta', {
        'lastmodifieddate': datetime.now().isoformat()
    })
    ET.SubElement(meta, 'creator').text = 'SIF to GEXF Converter'
    ET.SubElement(meta, 'description').text = sif['summary']['text']
    
    # Create graph
    graph = ET.SubElement(gexf, 'graph', {
        'defaultedgetype': 'directed',
        'mode': 'static'
    })
    
    # Define node attributes
    attributes_node = ET.SubElement(graph, 'attributes', {'class': 'node'})
    ET.SubElement(attributes_node, 'attribute', {
        'id': '0',
        'title': 'importance',
        'type': 'float'
    })
    ET.SubElement(attributes_node, 'attribute', {
        'id': '1',
        'title': 'scene',
        'type': 'string'
    })
    ET.SubElement(attributes_node, 'attribute', {
        'id': '2',
        'title': 'emerged',
        'type': 'string'
    })
    ET.SubElement(attributes_node, 'attribute', {
        'id': '3',
        'title': 'description',
        'type': 'string'
    })
    
    # Add nodes (entities)
    nodes = ET.SubElement(graph, 'nodes')
    for entity in sif['entities']:
        node = ET.SubElement(nodes, 'node', {
            'id': entity['id'],
            'label': entity['name']
        })
        
        # Add attributes
        attvalues = ET.SubElement(node, 'attvalues')
        ET.SubElement(attvalues, 'attvalue', {
            'for': '0',
            'value': str(entity['importance'])
        })
        ET.SubElement(attvalues, 'attvalue', {
            'for': '1',
            'value': entity['attributes'].get('scene', '')
        })
        ET.SubElement(attvalues, 'attvalue', {
            'for': '2',
            'value': entity['attributes'].get('emerged', '')
        })
        ET.SubElement(attvalues, 'attvalue', {
            'for': '3',
            'value': entity.get('description', '')
        })
    
    # Add edges (relationships)
    edges = ET.SubElement(graph, 'edges')
    for i, rel in enumerate(sif['relationships']):
        ET.SubElement(edges, 'edge', {
            'id': str(i),
            'source': rel['entity_a'],
            'target': rel['entity_b'],
            'weight': str(rel.get('strength', 1.0))
        })
    
    # Pretty print
    xml_str = ET.tostring(gexf, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ')


def main():
    parser = argparse.ArgumentParser(description='Convert SIF to Gephi GEXF format')
    parser.add_argument('--input', type=Path, required=True, help='Input SIF file')
    parser.add_argument('--output', type=Path, required=True, help='Output GEXF file')
    
    args = parser.parse_args()
    
    print(f"📊 Converting {args.input} to Gephi format...")
    
    # Load SIF
    with open(args.input, 'r', encoding='utf-8') as f:
        sif = json.load(f)
    
    print(f"  → {len(sif['entities'])} entities")
    print(f"  → {len(sif['relationships'])} relationships")
    
    # Convert to GEXF
    gexf_xml = sif_to_gexf(sif)
    
    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(gexf_xml)
    
    print(f"✅ Wrote {args.output}")
    print()
    print("💜 Ready to visualize in Gephi!")


if __name__ == '__main__':
    main()
