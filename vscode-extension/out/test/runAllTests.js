"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
// Mock vscode module for standalone node test execution
const Module = require('module');
const originalRequire = Module.prototype.require;
Module.prototype.require = function (request) {
    if (request === 'vscode') {
        return {
            workspace: {
                workspaceFolders: [{ uri: { fsPath: process.cwd() }, name: 'WIA-Test-Workspace' }],
                getConfiguration: () => ({ get: () => '' })
            },
            window: {
                createTerminal: () => ({ show: () => { }, sendText: () => { }, dispose: () => { } }),
                showInformationMessage: () => Promise.resolve(),
                showWarningMessage: () => Promise.resolve(),
                showErrorMessage: () => Promise.resolve()
            },
            Uri: { file: (p) => ({ fsPath: p }) }
        };
    }
    return originalRequire.apply(this, arguments);
};
const jevRouting_test_1 = require("./jevRouting.test");
const healthModel_test_1 = require("./healthModel.test");
const agentExecution_test_1 = require("./agentExecution.test");
const responseFormatter_test_1 = require("./responseFormatter.test");
function runAll() {
    console.log('========================================');
    console.log(' running WIA Extension Test Suites');
    console.log('========================================\n');
    const jev = (0, jevRouting_test_1.runJEVRoutingTests)();
    for (const r of jev.results)
        console.log(r);
    console.log('\n--- Health Model Tests ---');
    const health = (0, healthModel_test_1.runHealthModelTests)();
    for (const r of health.results)
        console.log(r);
    console.log('\n--- Agent Execution & Pipeline Tests ---');
    const agent = (0, agentExecution_test_1.runAgentExecutionTests)();
    for (const r of agent.results)
        console.log(r);
    console.log('\n--- Response Formatter Tests ---');
    const formatter = (0, responseFormatter_test_1.runResponseFormatterTests)();
    for (const r of formatter.results)
        console.log(r);
    const totalPassed = jev.passed + health.passed + agent.passed + formatter.passed;
    const totalFailed = jev.failed + health.failed + agent.failed + formatter.failed;
    console.log('\n========================================');
    console.log(` ALL TESTS COMPLETED: ${totalPassed} Passed, ${totalFailed} Failed`);
    console.log('========================================');
    if (totalFailed > 0) {
        process.exit(1);
    }
}
runAll();
//# sourceMappingURL=runAllTests.js.map