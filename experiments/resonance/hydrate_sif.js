const fs = require('fs');
const path = require('path');

// Config
const MAP_FILE = 'enao_resonance_map.json';
const SHARDS_DIR = '../../data/en_music'; // The target directory to hydrate

async function main() {
    console.log("💧 Hydrating ENAO Shards with Prime Signatures...");

    // 1. Load the Map
    if (!fs.existsSync(MAP_FILE)) {
        console.error(`❌ Map file not found: ${MAP_FILE}`);
        return;
    }
    const mapData = JSON.parse(fs.readFileSync(MAP_FILE, 'utf8'));
    const vocabulary = mapData.vocabulary; // Genre -> [Primes]
    console.log(`📚 Loaded vocabulary for ${Object.keys(vocabulary).length} genres.`);

    // 2. Iterate Shards
    const files = fs.readdirSync(SHARDS_DIR).filter(f => f.endsWith('.sif.json'));

    let totalUpdated = 0;

    for (const file of files) {
        if (file.includes('hierarchical_shards')) continue; // Skip master index, only hydrate content shards

        const filePath = path.join(SHARDS_DIR, file);
        const shard = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        let shardUpdated = 0;

        // 3. Update Entities
        for (const entity of shard.entities) {
            if (entity.type === 'genre') {
                const name = entity.name.toLowerCase();
                if (vocabulary[name]) {
                    entity.prime_signature = vocabulary[name];
                    shardUpdated++;
                    totalUpdated++;
                }
            }
        }

        if (shardUpdated > 0) {
            fs.writeFileSync(filePath, JSON.stringify(shard, null, 2));
            console.log(`   ✅ Hydrated ${shardUpdated} genres in ${file}`);
        }
    }

    console.log(`✨ DONE. Total entities updated: ${totalUpdated}`);
}

main().catch(err => console.error(err));
