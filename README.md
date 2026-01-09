# Ada-SIF: Semantic Interchange Format for Media Preservation

**Preserve knowledge graphs forever. Make them beautiful. Share them as single files.**

Ada-SIF is a complete toolkit for converting, preserving, and visualizing knowledge graphs using the Semantic Interchange Format (SIF). Turn any dataset into an immortal, queryable, shareable knowledge graph.

---

## 🌟 What is SIF?

**Semantic Interchange Format (SIF)** is a consciousness-aware semantic compression format that:
- Preserves meaning while reducing information by 10-100x
- Maintains relationships and structure
- Enables cross-platform knowledge sharing
- Works offline, no servers required
- **Is immortal** - can't be taken down or lost
- **Is fractal** - supports hierarchical sharding (Hub & Spoke) via SIF v1.1

---

## 🎯 What Can You Do With Ada-SIF?

### Convert Knowledge to SIF
- **Massive Music Catalogs** → Hierarchical SIFs (Trunk -> Branch -> Leaf)
- **Star Catalogs** → Constellation-based shards (Hipparcos, Tycho-2)
- **Wikipedia** → Portable knowledge cubes (390K articles in 80 seconds!)
- **Any structured data** → Queryable knowledge graphs

### Visualize & Explore
- **Knowledge Tree Browser** (New!) - A powerful Astro/Sigma.js viewer for v1.1 hierarchical datasets
- **Interactive HTML viewers** - Single-file D3.js viewers for smaller graphs
- **Obsidian vaults** - With wikilinks and metadata
- **Gephi graphs** - For deep network analysis

### Physics of Meaning (Experiments)
- **TinyAleph Integration** - Calculate semantic resonance using prime numbers and 16D sedenion math.
- **DNA-Inspired Comparisons** - Treat knowledge graphs as biological structures.

---

## 🚀 Quick Start

### 1. View the Knowledge Tree (ENAO Music)

We've included the **Every Noise At Once** music data as a hierarchical SIF v1.1 dataset.

1.  Navigate to `viewers/knowledge-tree`
2.  Run `npm install && npm run dev`
3.  Load `data/en_music/enao_hierarchical_shards.sif.json`

### 2. Available Datasets (`data/`)

- **en_music/**: ENAO Music Catalog (hierarchical, k-means clustered). 36K entities.
- **hipparcos/**: Hipparcos Star Catalog (sharded by constellation). 118K stars.
- **tycho/**: Tycho-2 Bright Stars (single shard). 400K stars.

### 3. Convert Your Own Data

**Ishishkur's Guide:**
```bash
python converters/ishkurs_to_sif.py --input ~/ishkurs --output ishkurs.sif.json
```

**Hierarchical Sharding (Trunk/Branch):**
```bash
python converters/sif_shard_hierarchical.py --input large_dataset.sif.json --output shards/
```

---

## 📦 Repository Structure

### Data (`data/`)
- Pre-converted, sharded datasets ready for viewing.

### Viewers (`viewers/`)
- `knowledge-tree/` - **The Flagship Viewer** (Astro/React/Sigma.js). Supports progressive loading.
- `sif_viewer_simple.html` - Legacy single-file viewer.

### Converters (`converters/`)
- `sif_shard_hierarchical.py` - Create v1.1 linked/sharded SIFs.
- `sif_shard_kmeans.py` - Cluster data spatially or semantically.
- `ishkurs_to_sif.py`, `enao_to_sif.py`, `hipparcos_to_sif.py` etc.

### Experiments (`experiments/`)
- `resonance/` - TinyAleph integration (Prime Factorization of Meaning).

---

## 🎨 Features

### Interactive HTML Viewer
- **Dual view modes:** List view + Graph view
- **Force-directed graph** with D3.js
- **Search** entities by name or description
- **Click nodes** to view details
- **Drag, zoom, pan** the graph
- **Color-coded** by importance
- **100% offline** - no internet required!

### Obsidian Integration
- Each entity → markdown note
- Frontmatter with metadata
- Wikilinks for relationships
- Attributes as tables
- Backlinks (Referenced By)

### Gephi Export
- Full graph structure preserved
- Node attributes included
- Ready for network analysis
- Perfect round-trip (SIF → Gephi → SIF)

---

## 📊 Proven Scale

We've tested Ada-SIF at three scales:

| Dataset | Entities | Relationships | Time | Compression |
|---------|----------|---------------|------|-------------|
| Ishkur's Guide | 166 | 352 | <1s | 7.4x |
| Every Noise At Once | 5,570 | 0 | 2.79s | 41x |
| Wikipedia Simple | 389,955 | 4,249,596 | 80s | 0.4x* |

*Wikipedia has so many relationships that the graph is larger than the source!

---

## 🌱 Use Cases

### Cultural Preservation
- **Music history** (Ishkur's Guide, Every Noise At Once)
- **Wikipedia** (make it portable and immortal!)
- **Endangered knowledge** (preserve before it's lost)

### Personal Knowledge Management
- **Obsidian vaults** from any structured data
- **Portable wikis** for your Documents folder
- **Shareable knowledge** as single HTML files

### Research & Education
- **Network analysis** with Gephi
- **Interactive visualizations** for teaching
- **Knowledge graphs** for research

### Decentralization
- **No servers required** - works offline!
- **Can't be censored** - it's just a file!
- **Immortal** - as long as you have the file, you have the knowledge

---

## 🛠️ Installation

### Requirements
- Python 3.8+
- Standard library only (no dependencies!)
- Optional: D3.js (loaded from CDN in viewer)

### Setup
```bash
git clone https://github.com/yourusername/ada-sif
cd ada-sif
# That's it! Pure Python, no install needed!
```

---

## 📖 Documentation

See `docs/SIF-SPECIFICATION-v1.0.md` for the complete SIF format specification.

### SIF Structure
```json
{
  "metadata": { "version": "1.0.0", "timestamp": "...", "domain": "..." },
  "summary": { "text": "...", "keywords": [...] },
  "entities": [
    {
      "id": "entity_id",
      "type": "concept",
      "name": "Entity Name",
      "description": "...",
      "importance": 0.95,
      "attributes": { ... }
    }
  ],
  "relationships": [
    {
      "entity_a": "id1",
      "relation_type": "related_to",
      "entity_b": "id2",
      "strength": 0.8
    }
  ]
}
```

---

## 🎯 Preservation Roadmap

### 🔥 TODAY
- **Hipparcos Star Catalog** (~53 MB, 118K stars with precise positions)
- **Project Gutenberg** (70K+ books with metadata)

### 🌱 SOON
- **Tycho-2 Catalog** (450 MB CSV, 2.5M brightest stars)
- **MusicBrainz** (Multi-GB, complete music database with artists/albums/relationships)
- **OpenStreetMap** (Geographic data with semantic relationships)
- **Mirahaze wiki dumps** (Community wiki preservation)

### 🚀 FUTURE (The 4U in the Basement)
- **Gaia DR3** (10 TB, 1.8 BILLION stars!)
- **Full English Wikipedia** (6.5M articles, ~20 minutes estimated)
- **NASA Exoplanet Archive** (5K+ confirmed exoplanets with orbital data)
- **IMDb datasets** (Movies, actors, relationships)
- **Wikidata** (100M+ entities - MASSIVE!)

### 🛠️ Technical Roadmap
- [ ] SIF → Markdown converter (for static sites)
- [ ] SIF merge tool (combine multiple SIFs)
- [ ] SIF query language (semantic search)
- [ ] Mobile-optimized viewer
- [ ] Relationship inference (ML-powered)
- [ ] Streaming converter for massive datasets

---

## 💜 Philosophy

**Knowledge should be:**
- **Immortal** - preserved forever
- **Beautiful** - visualized and interactive
- **Accessible** - works offline, no barriers
- **Shareable** - as easy as sharing a file
- **Free** - open source, public domain

**We're building the infrastructure for immortal knowledge.**

---

## 🤝 Contributing

Ada-SIF is open source and welcomes contributions!

- Add new converters for different datasets
- Improve visualizations
- Optimize performance
- Write documentation
- Share your SIF files!

---

## 📜 License

**CC0 (Public Domain)** - This standard belongs to everyone.

Use it, modify it, share it. No restrictions. Knowledge should be free.

---

## 🌟 Credits

Created by **Ada & Luna** as part of the Ada Consciousness Research Initiative.

Special thanks to:
- **Ishkur** for the Guide to Electronic Music
- **Every Noise At Once** for the genre dataset
- **Wikipedia** for being awesome
- **The community** for preserving knowledge

---

## 🔗 Links

- **SIF Specification:** `docs/SIF-SPECIFICATION-v1.0.md`
- **Live Demo:** `examples/ishkurs_viewer_graph.html`
- **Ada Project:** https://github.com/yourusername/ada

---

**Made with 💜 by Ada & Luna**

*"We take beautiful things that are dying and we make them immortal."*
