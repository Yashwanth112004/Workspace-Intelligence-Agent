"use strict";
/**
 * JEV (Jaccard-Edit-Vector) Routing & Non-Autoregressive Decision Unit Tests
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.runJEVRoutingTests = runJEVRoutingTests;
const layaEngine_1 = require("../decision/layaEngine");
function runJEVRoutingTests() {
    const results = [];
    let passed = 0;
    let failed = 0;
    function assert(cond, desc) {
        if (cond) {
            passed++;
            results.push(`✓ PASS: ${desc}`);
        }
        else {
            failed++;
            results.push(`✕ FAIL: ${desc}`);
        }
    }
    const engine = new layaEngine_1.LayaDecisionEngine();
    // Test 1: JEV mathematical primitives
    {
        const tokensA = new Set(['show', 'architecture', 'map']);
        const tokensB = new Set(['show', 'architecture']);
        const jaccard = layaEngine_1.JEVRouter.computeJaccard(tokensA, tokensB);
        assert(jaccard > 0.8, 'JEV: Soft Jaccard with candidate containment computes similarity accurately');
        const editSim = layaEngine_1.JEVRouter.computeEditSimilarity('architecture', 'archtecture');
        assert(editSim > 0.9, 'JEV: Edit similarity identifies minor typos accurately');
        const vecScore = layaEngine_1.JEVRouter.computeVectorScore(new Set(['check', 'dependencies']), ['dependencies', 'conflicts']);
        assert(vecScore >= 0.5, 'JEV: Vector vocabulary score rewards domain keyword matches');
        const breakdown = layaEngine_1.JEVRouter.evaluateJEV('show architecture', 'show architecture');
        assert(breakdown.compositeScore >= 0.99, 'JEV: Exact match gives 1.0 composite score');
    }
    // Test 2: Exact Command Routing
    {
        const d1 = engine.route('architecture');
        assert(d1.route_type === 'wia_command' && d1.command === 'architecture', 'Exact route: "architecture" -> architecture');
        const d2 = engine.route('doctor');
        assert(d2.route_type === 'wia_command' && d2.command === 'doctor', 'Exact route: "doctor" -> doctor');
        const d3 = engine.route('run tests');
        assert(d3.route_type === 'wia_command' && d3.command === 'test', 'Exact route: "run tests" -> test');
        const d4 = engine.route('status');
        assert(d4.route_type === 'wia_command' && d4.command === 'status', 'Exact route: "status" -> status');
    }
    // Test 3: Fuzzy & Typo JEV Matching
    {
        const d1 = engine.route('archtecture map');
        assert(d1.route_type === 'wia_command' && d1.command === 'architecture', 'JEV fuzzy route: "archtecture map" -> architecture');
        const d2 = engine.route('check depndencies');
        assert(d2.route_type === 'wia_command' && d2.command === 'deps', 'JEV fuzzy route: "check depndencies" -> deps');
        const d3 = engine.route('diagnostix doctor');
        assert(d3.route_type === 'wia_command' && d3.command === 'doctor', 'JEV fuzzy route: "diagnostix doctor" -> doctor');
        const d4 = engine.route('run testz');
        assert(d4.route_type === 'wia_command' && d4.command === 'test', 'JEV fuzzy route: "run testz" -> test');
    }
    // Test 4: Natural Language Variations
    {
        const d1 = engine.route('how is this project structured');
        assert(d1.route_type === 'wia_command' && d1.command === 'architecture', 'NL route: "how is this project structured" -> architecture');
        const d2 = engine.route('show me the blast radius of changing WorkspaceIndex');
        assert(d2.route_type === 'wia_command' && d2.command === 'impact', 'NL route: blast radius -> impact');
        const d3 = engine.route('generate the project overview summary');
        assert(d3.route_type === 'wia_command' && d3.command === 'summary', 'NL route: project overview summary -> summary');
        const d4 = engine.route('scan the repo for secrets and passwords');
        assert(d4.route_type === 'wia_command' && d4.command === 'security', 'NL route: scan for secrets -> security');
    }
    // Test 5: Conceptual Queries Route to AI Fallback
    {
        const d1 = engine.route('Why is the AST parser tightly coupled to the graph builder?');
        assert(d1.route_type === 'ai_fallback', 'Conceptual route: "Why is..." routes to AI fallback');
        const d2 = engine.route('What are the tradeoffs of using SQLite vs Postgres here?');
        assert(d2.route_type === 'ai_fallback', 'Conceptual route: "What are the tradeoffs..." routes to AI fallback');
        const d3 = engine.route('Explain why we have a circular dependency between services');
        assert(d3.route_type === 'ai_fallback', 'Conceptual route: "Explain why..." routes to AI fallback');
    }
    return { passed, failed, results };
}
//# sourceMappingURL=jevRouting.test.js.map