const fs = require('fs');
const path = require('path');
const { SemanticBackend } = require('@aleph-ai/tinyaleph');
// Helper: Simple Prime Generator
function* primeGenerator(start = 2) {
    let n = start;
    const isPrime = num => {
        for (let i = 2, s = Math.sqrt(num); i <= s; i++)
            if (num % i === 0) return false;
        return num > 1;
    };
    while (true) {
        if (isPrime(n)) yield n;
        n++;
    }
}

// Configuration
const MASTER_INDEX_PATH = '../enao-recursive/hierarchical_shards/enao_hierarchical_shards.sif.json';
const OUTPUT_FILE = 'enao_resonance_map.json';

async function main() {
    console.log("🌌 SIF-to-TinyAleph Bridge Starting...");

    // 1. Load Master Index
    const masterPath = path.resolve(__dirname, MASTER_INDEX_PATH);
    if (!fs.existsSync(masterPath)) {
        console.error(`❌ Master index not found at ${masterPath}`);
        return;
    }
    const master = JSON.parse(fs.readFileSync(masterPath, 'utf8'));
    console.log(`📚 Loaded Master Index: ${master.shards.length} shards`);

    // 2. Initialize Ontology Map
    const ontology = {}; // Prime -> Meaning (e.g., 2 -> "Cluster 0")
    const genrePrimes = {}; // GenreID -> [Primes]

    // Generator for Cluster Primes (2, 3, 5, 7...)
    const clusterPrimeGen = primeGenerator(2);

    // 3. Process Clusters (Branches)
    // Each cluster gets a base prime.
    for (const shard of master.shards) {
        if (shard.type !== 'branch' && shard.type !== 'module') continue;

        // Assign a Prime to this Cluster
        const clusterPrime = clusterPrimeGen.next().value;
        ontology[clusterPrime] = `Cluster: ${shard.name}`;
        console.log(`   🔹 Assigned Prime ${clusterPrime} to Cluster '${shard.name}'`);

        // Load the shard content to find genres
        const shardPath = path.resolve(path.dirname(masterPath), shard.url);
        const shardData = JSON.parse(fs.readFileSync(shardPath, 'utf8'));

        // Generator for Genre Primes WITHIN this cluster (starts higher to avoid collision with low primes)
        // Ideally, we'd use a unique prime for every genre globally, 
        // but for now, let's just pretend we combine ClusterPrime * UniqueGenrePrime
        let genreLocalPrime = 101;

        for (const entity of shardData.entities) {
            if (entity.type === 'genre') {
                // Find next prime for this genre
                // In a real system, we'd ensure global uniqueness, but let's just make it distinct
                // To keep numbers smallish, we'll use a simple increment for the 'local' part 
                // and rely on TinyAleph's factoring. 
                // Wait, TinyAleph WANTS a list of primes.

                // So Genre Signature = [ClusterPrime, LocalUniquePrime]
                // We need a generator that just gives us the next prime.
                const pGen = primeGenerator(genreLocalPrime);
                const localPrime = pGen.next().value;
                genreLocalPrime = localPrime + 1; // Advance start

                const signature = [clusterPrime, localPrime];
                genrePrimes[entity.name.toLowerCase()] = signature;

                // Track in ontology
                ontology[localPrime] = `Genre: ${entity.name}`;
            }
        }
    }

    console.log(`✅ Mapped ${Object.keys(genrePrimes).length} genres to prime signatures.`);

    // 4. Initialize TinyAleph with this Ontology
    console.log("\n🧪 initializing SemanticBackend with SIF Ontology...");
    const backend = new SemanticBackend({
        ontology: ontology,
        vocabulary: genrePrimes, // Direct mapping: Word -> Primes
    });

    // 5. Test Resonance
    console.log("\n🎻 Testing Resonance on Mapped Genres:");

    // Helper to test
    const compare = (g1, g2) => {
        const s1 = backend.textToOrderedState(g1);
        const s2 = backend.textToOrderedState(g2);
        const coherence = s1.coherence(s2);
        console.log(`   '${g1}' <-> '${g2}' = ${coherence.toFixed(4)}`);
    };

    // Pick some genres we know are in specific clusters
    // We need to know which genres ended up in which clusters.
    // Let's just pick keys from our map.
    const genres = Object.keys(genrePrimes);
    if (genres.length > 50) {
        const gA = genres[0];
        const gB = genres[1]; // Likely same cluster
        const gZ = genres[genres.length - 1]; // Likely different cluster

        console.log(`   (Using raw vocabulary lookups...)`);
        compare(gA, gB);
        compare(gA, gZ);
    }

    // Save the map
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify({ ontology, vocabulary: genrePrimes }, null, 2));
    console.log(`\n💾 Saved Resonance Map to ${OUTPUT_FILE}`);
}

main().catch(err => console.error(err));
