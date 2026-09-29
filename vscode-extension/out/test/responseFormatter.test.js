"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.runResponseFormatterTests = runResponseFormatterTests;
const responseFormatter_1 = require("../formatting/responseFormatter");
function runResponseFormatterTests() {
    let passed = 0;
    let failed = 0;
    const results = [];
    function test(name, fn) {
        try {
            if (fn()) {
                passed++;
                results.push(`✓ PASS: Formatter: ${name}`);
            }
            else {
                failed++;
                results.push(`✗ FAIL: Formatter: ${name}`);
            }
        }
        catch (err) {
            failed++;
            results.push(`✗ ERROR: Formatter: ${name} (${err.message})`);
        }
    }
    // 1. Impact Formatting
    test('Formats impact analysis with structured sections', () => {
        const rawImpact = `=== Impact Analysis for 'agentViewProvider.ts' ===
  Target Entity: agentViewProvider.ts
  Defined In: vscode-extension/src/providers/agentViewProvider.ts
  Target Type: module
  Risk Classification: HIGH
  Explanation: High blast radius: 12 total downstream files depend on this module.

=== Direct Symbol Callers ===
  * src/extension.ts::activate (CALLS)
  * src/panels/WiaChatPanel.ts (CALLS)

=== Affected Files (12) ===
  * vscode-extension/src/extension.ts
  * vscode-extension/src/panels/WiaChatPanel.ts
  * vscode-extension/src/panels/WiaArchitecturePanel.ts`;
        const formatted = responseFormatter_1.WiaResponseFormatter.formatResponse(rawImpact, 'what is the impact of agentViewProvider.ts', 'impact');
        return (formatted.includes('## Impact Analysis') &&
            formatted.includes('### Target') &&
            formatted.includes('`agentViewProvider.ts`') &&
            formatted.includes('### Risk') &&
            formatted.includes('**HIGH RISK**') &&
            formatted.includes('### Direct Impact') &&
            formatted.includes('`src/extension.ts::activate (CALLS)`') &&
            formatted.includes('### Downstream Impact') &&
            formatted.includes('### Explanation') &&
            formatted.includes('### Summary'));
    });
    // 2. Architecture Formatting
    test('Formats architecture output into standard sections', () => {
        const rawArch = `=== Architecture Intelligence for 'Workspace-Intelligence-Agent' ===
ARCHITECTURE SUMMARY
The repository is a Python and TypeScript application.

=== Architectural Subsystems ===
  * CLI Presentation (` + '`wia/cli/`' + `)
    - Role: CLI Entrypoint

=== Inter-Component Dependency Flow ===
  CLI -> Services -> Core

=== Application Entry Points ===
  * ` + '`wia`' + ` -> ` + '`wia.cli.app:cli_entrypoint`' + ``;
        const formatted = responseFormatter_1.WiaResponseFormatter.formatResponse(rawArch, 'Show architecture', 'architecture');
        return (formatted.includes('## Architecture') &&
            formatted.includes('### Overview') &&
            formatted.includes('### Components') &&
            formatted.includes('### Relationships') &&
            formatted.includes('### Execution Flow'));
    });
    // 3. Project Overview Formatting
    test('Formats project overview for explain queries', () => {
        const rawExplain = `=== Workspace Summary ===
Workspace Intelligence Agent provides deterministic AST indexing and LLM reasoning.

=== Architectural Subsystems ===
  * Core Services (` + '`wia/services/`' + `)

=== High Fan-In Components (Shared Utilities) ===
  * ` + '`wia/core/index_model.py`' + ` (Fan-In: 34)`;
        const formatted = responseFormatter_1.WiaResponseFormatter.formatResponse(rawExplain, 'Explain this project', 'summary');
        return (formatted.includes('## Project Overview') &&
            formatted.includes('### Purpose') &&
            formatted.includes('### Architecture') &&
            formatted.includes('### Main Components') &&
            formatted.includes('### Summary'));
    });
    // 4. Dependencies Formatting
    test('Formats dependencies output', () => {
        const rawDeps = `=== Package Manifests ===
pyproject.toml, package.json

=== Dependency Conflicts ===
None detected.`;
        const formatted = responseFormatter_1.WiaResponseFormatter.formatResponse(rawDeps, 'Check dependencies', 'deps');
        return (formatted.includes('## Dependencies') &&
            formatted.includes('### Runtime Dependencies') &&
            formatted.includes('### Internal Dependencies'));
    });
    // 5. Environment Formatting
    test('Formats environment health output', () => {
        const rawEnv = `=== WIA Doctor ===
Runtime: Python 3.11.9
Platform: Windows-10`;
        const formatted = responseFormatter_1.WiaResponseFormatter.formatResponse(rawEnv, 'Check environment', 'doctor');
        return (formatted.includes('## Environment') &&
            formatted.includes('### Runtime') &&
            formatted.includes('### Configuration') &&
            formatted.includes('### Required Tools'));
    });
    return { passed, failed, results };
}
//# sourceMappingURL=responseFormatter.test.js.map