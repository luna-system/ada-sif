#!/usr/bin/env python3
"""
SIF → Obsidian Converter
=========================

Converts SIF knowledge graphs into Obsidian vaults.

Each entity becomes a markdown note with:
- Frontmatter (metadata)
- Description
- Attributes table
- Links to related entities

Usage:
    python sif_to_obsidian.py --input simplewiki.sif.json --output obsidian-vault/
"""

import json
import re
from pathlib import Path
from typing import Dict, List
import argparse


def sanitize_filename(name: str) -> str:
    """Convert entity name to valid filename."""
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Limit length
    if len(name) > 200:
        name = name[:200]
    return name.strip()


def entity_to_markdown(entity: Dict, relationships: List[Dict], entities_by_id: Dict) -> str:
    """Convert SIF entity to Obsidian markdown note."""
    
    # Frontmatter
    frontmatter = [
        '---',
        f'id: {entity["id"]}',
        f'type: {entity["type"]}',
        f'importance: {entity["importance"]:.3f}',
    ]
    
    # Add aliases if present
    if entity.get('aliases'):
        frontmatter.append(f'aliases: [{", ".join(entity["aliases"])}]')
    
    # Add custom attributes
    for key, value in entity.get('attributes', {}).items():
        if isinstance(value, (int, float, str)):
            frontmatter.append(f'{key}: {value}')
    
    frontmatter.append('---')
    frontmatter.append('')
    
    # Title
    content = [f'# {entity["name"]}', '']
    
    # Description
    if entity.get('description'):
        content.append(entity['description'])
        content.append('')
    
    # Attributes table (if any)
    attrs = entity.get('attributes', {})
    if attrs:
        content.append('## Attributes')
        content.append('')
        content.append('| Attribute | Value |')
        content.append('|-----------|-------|')
        for key, value in attrs.items():
            content.append(f'| {key} | {value} |')
        content.append('')
    
    # Outgoing relationships
    outgoing = [r for r in relationships if r['entity_a'] == entity['id']]
    if outgoing:
        content.append('## Related To')
        content.append('')
        
        # Group by relation type
        by_type = {}
        for rel in outgoing:
            rel_type = rel.get('relation_type', 'related_to')
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel)
        
        for rel_type, rels in by_type.items():
            content.append(f'### {rel_type.replace("_", " ").title()}')
            content.append('')
            for rel in rels[:100]:  # Limit to 100 links
                target = entities_by_id.get(rel['entity_b'])
                if target:
                    content.append(f'- [[{target["name"]}]]')
            if len(rels) > 100:
                content.append(f'- *(and {len(rels) - 100} more...)*')
            content.append('')
    
    # Incoming relationships (backlinks)
    incoming = [r for r in relationships if r['entity_b'] == entity['id']]
    if incoming:
        content.append('## Referenced By')
        content.append('')
        for rel in incoming[:50]:  # Limit to 50 backlinks
            source = entities_by_id.get(rel['entity_a'])
            if source:
                content.append(f'- [[{source["name"]}]]')
        if len(incoming) > 50:
            content.append(f'- *(and {len(incoming) - 50} more...)*')
        content.append('')
    
    return '\n'.join(frontmatter + content)


def create_obsidian_vault(sif: Dict, output_dir: Path, sample_size: int = None):
    """Convert SIF to Obsidian vault."""
    
    print(f"📝 Creating Obsidian vault at {output_dir}...")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create entities lookup
    entities_by_id = {e['id']: e for e in sif['entities']}
    
    # Determine which entities to convert
    entities_to_convert = sif['entities']
    if sample_size:
        entities_to_convert = entities_to_convert[:sample_size]
    
    # Convert each entity to markdown
    print(f"  Converting {len(entities_to_convert):,} entities...")
    for i, entity in enumerate(entities_to_convert):
        if i % 1000 == 0 and i > 0:
            print(f"    Processed {i:,} entities...")
        
        # Generate markdown
        markdown = entity_to_markdown(entity, sif['relationships'], entities_by_id)
        
        # Write to file
        filename = sanitize_filename(entity['name']) + '.md'
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
    
    # Create index/README
    readme = [
        f'# {sif["summary"]["text"]}',
        '',
        f'**Entities:** {len(sif["entities"]):,}',
        f'**Relationships:** {len(sif["relationships"]):,}',
        '',
        '## Top Entities by Importance',
        ''
    ]
    
    for entity in sorted(sif['entities'], key=lambda e: e['importance'], reverse=True)[:20]:
        readme.append(f'- [[{entity["name"]}]] ({entity["importance"]:.2f})')
    
    with open(output_dir / 'README.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(readme))
    
    print(f"  ✅ Created {len(entities_to_convert):,} markdown files")


def main():
    parser = argparse.ArgumentParser(description='Convert SIF to Obsidian vault')
    parser.add_argument('--input', type=Path, required=True, help='Input SIF file')
    parser.add_argument('--output', type=Path, required=True, help='Output directory for Obsidian vault')
    parser.add_argument('--sample', type=int, help='Sample size (for testing)')
    
    args = parser.parse_args()
    
    print("📚 Converting SIF to Obsidian vault...")
    print()
    
    # Load SIF
    with open(args.input, 'r', encoding='utf-8') as f:
        sif = json.load(f)
    
    # Create vault
    create_obsidian_vault(sif, args.output, args.sample)
    
    print()
    print("✅ Conversion complete!")
    print()
    print(f"Vault created at: {args.output}")
    print("Open this folder in Obsidian to browse the knowledge graph!")
    print()
    print("💜 Your SIF is now an Obsidian vault!")


if __name__ == '__main__':
    main()
