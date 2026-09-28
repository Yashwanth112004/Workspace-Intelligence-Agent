"use strict";
/**
 * Comprehensive Agent View & Execution Pipeline Unit Tests
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.runAgentExecutionTests = runAgentExecutionTests;
const layaEngine_1 = require("../decision/layaEngine");
const wiaCommandRegistry_1 = require("../registry/wiaCommandRegistry");
const apiClient_1 = require("../apiClient");
const wiaExecutor_1 = require("../executor/wiaExecutor");
const envRepair_1 = require("../environment/envRepair");
function runAgentExecutionTests() {
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
    const apiClient = new apiClient_1.WiaApiClient('http://127.0.0.1:8000');
    const executor = new wiaExecutor_1.WiaExecutor(apiClient);
    const layaEngine = new layaEngine_1.LayaDecisionEngine();
    const envRepair = new envRepair_1.EnvironmentRepairEngine(executor);
    // Test 1: Registry Integrity & Command Validation
    {
        const commands = ['ask', 'architecture', 'deps', 'status', 'doctor', 'summary', 'files', 'info', 'search', 'explain', 'impact', 'flow', 'diff', 'security', 'report', 'test', 'run', 'build', 'config'];
        for (const cmd of commands) {
            const def = (0, wiaCommandRegistry_1.getWIACommand)(cmd);
            assert(def !== undefined && def.name === cmd, `Registry contains canonical command '${cmd}'`);
        }
    }
    // Test 2: Project Command Detection
    {
        const detected = executor.detectProjectCommands(process.cwd());
        assert(detected !== null && typeof detected === 'object', 'Project command detector executes safely');
    }
    // Test 3: Environment Repair Engine Inspection
    {
        const report = envRepair.inspectEnvironment(process.cwd());
        assert(report !== null && typeof report.isHealthy === 'boolean', 'Environment repair inspector returns structured diagnostics');
    }
    // Test 4: Query Routing Decision Pipeline for Natural Language
    {
        const testQueries = [
            { query: 'Show architecture', expectedCmd: 'architecture' },
            { query: 'Check dependencies', expectedCmd: 'deps' },
            { query: 'Check environment health', expectedCmd: 'doctor' },
            { query: 'Show project status', expectedCmd: 'status' },
            { query: 'Generate codebase summary', expectedCmd: 'summary' },
            { query: 'Search symbol WorkspaceIndex', expectedCmd: 'search' },
            { query: 'Analyze refactoring impact of Symbol', expectedCmd: 'impact' },
            { query: 'Trace call flow of main', expectedCmd: 'flow' },
            { query: 'Audit git diff impact', expectedCmd: 'diff' },
            { query: 'Scan for secrets and vulnerabilities', expectedCmd: 'security' },
            { query: 'Generate HTML intelligence report', expectedCmd: 'report' },
            { query: 'Run test suite', expectedCmd: 'test' }
        ];
        for (const t of testQueries) {
            const decision = layaEngine.route(t.query, wiaCommandRegistry_1.CANONICAL_WIA_COMMAND_REGISTRY);
            assert(decision.route_type === 'wia_command' && decision.command === t.expectedCmd, `Laya JEV correctly routes "${t.query}" -> ${t.expectedCmd} (score: ${decision.confidence})`);
        }
    }
    // Test 5: Fallback LLM Semantic Routing for Open-Ended Technical Questions
    {
        const conceptualQueries = [
            'How should we refactor the caching layer to scale?',
            'What is the best architecture pattern for this service?',
            'Explain the design trade-offs between sync and async execution'
        ];
        for (const q of conceptualQueries) {
            const decision = layaEngine.route(q, wiaCommandRegistry_1.CANONICAL_WIA_COMMAND_REGISTRY);
            assert(decision.route_type === 'ai_fallback', `Laya JEV routes conceptual prompt "${q}" -> ai_fallback`);
        }
    }
    return { passed, failed, results };
}
if (require.main === module) {
    const res = runAgentExecutionTests();
    for (const r of res.results) {
        console.log(r);
    }
    console.log(`\nExecution Tests Summary: ${res.passed} passed, ${res.failed} failed.`);
    if (res.failed > 0)
        process.exit(1);
}
//# sourceMappingURL=agentExecution.test.js.map