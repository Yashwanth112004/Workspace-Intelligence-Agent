/**
 * Comprehensive Agent View & Execution Pipeline Unit Tests
 */

import { LayaDecisionEngine } from '../decision/layaEngine';
import { CANONICAL_WIA_COMMAND_REGISTRY, getWIACommand } from '../registry/wiaCommandRegistry';
import { WiaApiClient } from '../apiClient';
import { WiaExecutor } from '../executor/wiaExecutor';
import { EnvironmentRepairEngine } from '../environment/envRepair';

export function runAgentExecutionTests(): { passed: number; failed: number; results: string[] } {
    const results: string[] = [];
    let passed = 0;
    let failed = 0;

    function assert(cond: boolean, desc: string) {
        if (cond) {
            passed++;
            results.push(`✓ PASS: ${desc}`);
        } else {
            failed++;
            results.push(`✕ FAIL: ${desc}`);
        }
    }

    const apiClient = new WiaApiClient('http://127.0.0.1:8000');
    const executor = new WiaExecutor(apiClient);
    const layaEngine = new LayaDecisionEngine();
    const envRepair = new EnvironmentRepairEngine(executor);

    // Test 1: Registry Integrity & Command Validation
    {
        const commands = ['ask', 'architecture', 'deps', 'status', 'doctor', 'summary', 'files', 'info', 'search', 'explain', 'impact', 'flow', 'diff', 'security', 'report', 'test', 'run', 'build', 'config'];
        for (const cmd of commands) {
            const def = getWIACommand(cmd);
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
            const decision = layaEngine.route(t.query, CANONICAL_WIA_COMMAND_REGISTRY);
            assert(decision.route_type === 'wia_command' && decision.command === t.expectedCmd,
                `Laya JEV correctly routes "${t.query}" -> ${t.expectedCmd} (score: ${decision.confidence})`);
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
            const decision = layaEngine.route(q, CANONICAL_WIA_COMMAND_REGISTRY);
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
    if (res.failed > 0) process.exit(1);
}
