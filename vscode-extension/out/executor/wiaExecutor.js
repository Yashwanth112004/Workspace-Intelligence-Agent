"use strict";
/**
 * Central WIA Operation Executor.
 *
 * Validates operation names, boundaries, and Workspace Trust,
 * executes registered WIA operations, and returns structured result objects.
 * Arbitrary shell command execution is strictly prevented.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaExecutor = void 0;
const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const fs = require("fs");
const operationRegistry_1 = require("../registry/operationRegistry");
class WiaExecutor {
    apiClient;
    terminal = null;
    constructor(apiClient) {
        this.apiClient = apiClient;
    }
    /**
     * Detect actual runnable project commands from repository manifests (package.json, pyproject.toml, Makefile, Cargo.toml).
     */
    detectProjectCommands(workspaceRoot) {
        const detected = {};
        // 1. Node.js package.json detection
        const pkgPath = path.join(workspaceRoot, 'package.json');
        if (fs.existsSync(pkgPath)) {
            try {
                const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
                const scripts = pkg.scripts || {};
                if (scripts.dev)
                    detected.run = 'npm run dev';
                else if (scripts.start)
                    detected.run = 'npm start';
                else if (scripts.serve)
                    detected.run = 'npm run serve';
                if (scripts.build)
                    detected.build = 'npm run build';
                if (scripts.test)
                    detected.test = 'npm test';
                if (scripts.lint)
                    detected.lint = 'npm run lint';
            }
            catch (e) { }
        }
        // 2. Python pyproject.toml / requirements detection
        if (!detected.test) {
            const pyprojPath = path.join(workspaceRoot, 'pyproject.toml');
            const pytestIni = path.join(workspaceRoot, 'pytest.ini');
            const testsDir = path.join(workspaceRoot, 'tests');
            if (fs.existsSync(pyprojPath) || fs.existsSync(pytestIni) || fs.existsSync(testsDir)) {
                detected.test = 'pytest';
            }
        }
        if (!detected.run) {
            if (fs.existsSync(path.join(workspaceRoot, 'manage.py'))) {
                detected.run = 'python manage.py runserver';
            }
            else if (fs.existsSync(path.join(workspaceRoot, 'main.py'))) {
                detected.run = 'python main.py';
            }
            else if (fs.existsSync(path.join(workspaceRoot, 'app.py'))) {
                detected.run = 'python app.py';
            }
        }
        // 3. Rust Cargo detection
        if (fs.existsSync(path.join(workspaceRoot, 'Cargo.toml'))) {
            if (!detected.run)
                detected.run = 'cargo run';
            if (!detected.build)
                detected.build = 'cargo build';
            if (!detected.test)
                detected.test = 'cargo test';
        }
        // 4. Go detection
        if (fs.existsSync(path.join(workspaceRoot, 'go.mod'))) {
            if (!detected.run)
                detected.run = 'go run .';
            if (!detected.build)
                detected.build = 'go build';
            if (!detected.test)
                detected.test = 'go test ./...';
        }
        return detected;
    }
    /**
     * Execute a registered project command safely in the VS Code terminal.
     */
    executeInTerminal(command, name = 'WIA Project Command') {
        if (!this.terminal || this.terminal.exitStatus !== undefined) {
            this.terminal = vscode.window.createTerminal(name);
        }
        this.terminal.show();
        this.terminal.sendText(command);
    }
    /**
     * Execute a validated WIA operation call.
     */
    async executeOperation(call, workspaceRoot) {
        const startTime = Date.now();
        if (!(0, operationRegistry_1.isValidOperation)(call.name)) {
            return {
                operation: call.name,
                status: 'failed',
                duration_ms: Date.now() - startTime,
                result: null,
                errors: [`Operation '${call.name}' is not registered in the WIA security registry.`]
            };
        }
        const def = (0, operationRegistry_1.getOperationDefinition)(call.name);
        // Security check: Workspace trust
        if (def.requiresTrust && !vscode.workspace.isTrusted) {
            return {
                operation: call.name,
                status: 'cancelled',
                duration_ms: Date.now() - startTime,
                result: null,
                errors: ['Workspace is not trusted. Operation disallowed under VS Code Workspace Trust security policy.']
            };
        }
        // Handle project.* operations (run, build, test, lint)
        if (def.category === 'project') {
            const commands = this.detectProjectCommands(workspaceRoot);
            let cmdToRun;
            if (call.name === 'project.run')
                cmdToRun = commands.run;
            else if (call.name === 'project.build')
                cmdToRun = commands.build;
            else if (call.name === 'project.test')
                cmdToRun = commands.test;
            else if (call.name === 'project.lint')
                cmdToRun = commands.lint;
            if (!cmdToRun) {
                return {
                    operation: call.name,
                    status: 'failed',
                    duration_ms: Date.now() - startTime,
                    result: null,
                    errors: [`No ${call.name.replace('project.', '')} command could be detected from workspace manifest files.`]
                };
            }
            this.executeInTerminal(cmdToRun, `WIA: ${call.name}`);
            return {
                operation: call.name,
                status: 'completed',
                duration_ms: Date.now() - startTime,
                result: {
                    detected_command: cmdToRun,
                    execution_mode: 'vscode_terminal'
                },
                errors: []
            };
        }
        // Handle WIA CLI / Core intelligence operations
        try {
            const cliArgs = this.mapOperationToCliArgs(call, workspaceRoot);
            const cliResult = await this.runWiaCli(cliArgs, workspaceRoot);
            return {
                operation: call.name,
                status: cliResult.exitCode === 0 ? 'completed' : 'failed',
                duration_ms: Date.now() - startTime,
                result: cliResult.parsedData || cliResult.stdout,
                stdout: cliResult.stdout,
                stderr: cliResult.stderr,
                exitCode: cliResult.exitCode,
                errors: cliResult.exitCode === 0 ? [] : [cliResult.stderr || 'Command exited with non-zero status.']
            };
        }
        catch (e) {
            return {
                operation: call.name,
                status: 'failed',
                duration_ms: Date.now() - startTime,
                result: null,
                errors: [e.message || String(e)]
            };
        }
    }
    mapOperationToCliArgs(call, _workspaceRoot) {
        const p = call.parameters || {};
        switch (call.name) {
            case 'workspace.scan':
                return ['index'];
            case 'workspace.summary':
                return ['summary'];
            case 'workspace.status':
                return ['status'];
            case 'repository.files':
                return ['files'];
            case 'repository.structure':
            case 'architecture.analyze':
                return ['architecture'];
            case 'index.search':
            case 'index.symbols':
                return ['search', p.query || p.symbol || 'main'];
            case 'component.explain':
                return ['explain', p.file_path || p.query || p.symbol || 'wia/core/retrieval.py'];
            case 'impact.analyze':
            case 'index.dependencies':
                return ['impact', p.symbol || p.file_path || 'WorkspaceIndex'];
            case 'environment.detect':
            case 'environment.check':
            case 'dependency.check':
            case 'dependency.conflicts':
            case 'dependency.missing':
                return ['doctor'];
            default:
                return ['summary'];
        }
    }
    runWiaCli(args, cwd) {
        return new Promise((resolve) => {
            // Run `wia <args>` or fallback to `python -m wia <args>`
            const isWin = process.platform === 'win32';
            const cmd = isWin ? 'wia' : 'wia';
            cp.execFile(cmd, args, { cwd, timeout: 30000 }, (err, stdout, stderr) => {
                if (err && !stdout) {
                    // Fallback to python -m wia
                    cp.execFile('python', ['-m', 'wia', ...args], { cwd, timeout: 30000 }, (pyErr, pyStdout, pyStderr) => {
                        let parsed;
                        try {
                            parsed = JSON.parse(pyStdout.trim());
                        }
                        catch (e) { }
                        resolve({
                            stdout: pyStdout,
                            stderr: pyStderr,
                            exitCode: pyErr ? (typeof pyErr.code === 'number' ? pyErr.code : 1) : 0,
                            parsedData: parsed
                        });
                    });
                    return;
                }
                let parsed;
                try {
                    parsed = JSON.parse(stdout.trim());
                }
                catch (e) { }
                resolve({
                    stdout: stdout || '',
                    stderr: stderr || '',
                    exitCode: err ? (typeof err.code === 'number' ? err.code : 1) : 0,
                    parsedData: parsed
                });
            });
        });
    }
}
exports.WiaExecutor = WiaExecutor;
//# sourceMappingURL=wiaExecutor.js.map