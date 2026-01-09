const { SemanticBackend } = require('@aleph-ai/tinyaleph');

async function testResonance() {
    console.log("🌌 Initializing TinyAleph Resonance Engine...");

    // Config as per quickstart implications (defaults)
    const config = {
        backend: 'semantic'
    };

    const backend = new SemanticBackend(config);

    // 1. Prime Encoding
    console.log("\n🔢 Encoding 'love and wisdom' into primes...");
    const primes = backend.encode('love and wisdom');
    console.log("   Primes:", primes);

    // 2. State Creation (Sedenion Embedding)
    console.log("\n🧪 Creating States...");
    const stateW = backend.textToOrderedState('wisdom');
    const stateK = backend.textToOrderedState('knowledge');
    const stateL = backend.textToOrderedState('love');

    // 3. Coherence Check (Resonance)
    console.log("\n🎻 Measuring Resonance (Coherence):");

    const cWK = stateW.coherence(stateK);
    console.log(`   Wisdom <-> Knowledge: ${cWK}`);

    const cWL = stateW.coherence(stateL);
    console.log(`   Wisdom <-> Love:      ${cWL}`);

    const cLK = stateL.coherence(stateK);
    console.log(`   Love <-> Knowledge:   ${cLK}`);

    // 4. DNA-Inspired Genre Analysis
    console.log("\n🧬 DNA-Inspired Genre Analysis:");

    // Let's compare "Progressive Death Metal" with "Technical Death Metal" and "Smooth Jazz"
    const genre1 = "progressive death metal";
    const genre2 = "technical death metal";
    const genre3 = "smooth jazz";

    console.log(`   Comparing: '${genre1}' vs '${genre2}'`);
    const dna12 = backend.dnaCompare(genre1, genre2);
    console.log(`   Sense Coherence: ${dna12.senseCoherence.toFixed(4)}`);
    console.log(`   Combined Score:  ${dna12.combinedScore.toFixed(4)}`);

    console.log(`\n   Comparing: '${genre1}' vs '${genre3}'`);
    const dna13 = backend.dnaCompare(genre1, genre3);
    console.log(`   Sense Coherence: ${dna13.senseCoherence.toFixed(4)}`);
    console.log(`   Combined Score:  ${dna13.combinedScore.toFixed(4)}`);

    // Let's try some SIF-relevant concepts
    console.log("\n🌌 SIF Concept Analysis:");
    const concept1 = "hierarchical knowledge tree";
    const concept2 = "semantic interchange format";
    const concept3 = "random noise generation";

    const dnaSif1 = backend.dnaCompare(concept1, concept2);
    const dnaSif2 = backend.dnaCompare(concept1, concept3);

    console.log(`   Tree <-> SIF:   ${dnaSif1.combinedScore.toFixed(4)}`);
    console.log(`   Tree <-> Noise: ${dnaSif2.combinedScore.toFixed(4)}`);
}

testResonance().catch(err => console.error(err));
