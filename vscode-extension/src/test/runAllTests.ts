// Mock vscode module for standalone node test execution
const Module = require('module');
const originalRequire = Module.prototype.require;
Module.prototype.require = function(request: string) {
    if (request === 'vscode') {
        return {
            workspace: {
                workspaceFolders: [{ uri: { fsPath: process.cwd() }, name: 'WIA-Test-Workspace' }],
                getConfiguration: () => ({ get: () => '' })
            },
            window: {
                createTerminal: () => ({ show: () => {}, sendText: () => {}, dispose: () => {} }),
                showInformationMessage: () => Promise.resolve(),
                showWarningMessage: () => Promise.resolve(),
                showErrorMessage: () => Promise.resolve()
            },
            Uri: { file: (p: string) => ({ fsPath: p }) }
        };
    }
    return originalRequire.apply(this, arguments);
};

import { runJEVRoutingTests } from './jevRouting.test';
import { runHealthModelTests } from './healthModel.test';
import { runAgentExecutionTests } from './agentExecution.test';

function runAll() {
    console.log('========================================');
    console.log(' running WIA Extension Test Suites');
    console.log('========================================\n');

    const jev = runJEVRoutingTests();
    for (const r of jev.results) console.log(r);

    console.log('\n--- Health Model Tests ---');
    const health = runHealthModelTests();
    for (const r of health.results) console.log(r);

    console.log('\n--- Agent Execution & Pipeline Tests ---');
    const agent = runAgentExecutionTests();
    for (const r of agent.results) console.log(r);

    const totalPassed = jev.passed + health.passed + agent.passed;
    const totalFailed = jev.failed + health.failed + agent.failed;

    console.log('\n========================================');
    console.log(` ALL TESTS COMPLETED: ${totalPassed} Passed, ${totalFailed} Failed`);
    console.log('========================================');

    if (totalFailed > 0) {
        process.exit(1);
    }
}

runAll();
