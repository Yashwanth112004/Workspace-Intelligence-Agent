"use strict";
/**
 * Environment Diagnostic and Repair Engine for WIA VS Code Extension.
 *
 * Inspects package managers, runtimes (Python/Node/Rust/Go), lockfiles,
 * and repairs missing dependencies without modifying global environments
 * or executing unvalidated shell injection.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.EnvironmentRepairEngine = void 0;
const path = require("path");
const fs = require("fs");
class EnvironmentRepairEngine {
    executor;
    constructor(executor) {
        this.executor = executor;
    }
    /**
     * Inspect environment health for the given workspace.
     */
    inspectEnvironment(workspaceRoot) {
        // 1. Node.js ecosystem
        if (fs.existsSync(path.join(workspaceRoot, 'package.json'))) {
            const hasLock = fs.existsSync(path.join(workspaceRoot, 'package-lock.json')) ||
                fs.existsSync(path.join(workspaceRoot, 'yarn.lock')) ||
                fs.existsSync(path.join(workspaceRoot, 'pnpm-lock.yaml'));
            const pm = fs.existsSync(path.join(workspaceRoot, 'pnpm-lock.yaml')) ? 'pnpm' :
                fs.existsSync(path.join(workspaceRoot, 'yarn.lock')) ? 'yarn' : 'npm';
            const nodeModulesExist = fs.existsSync(path.join(workspaceRoot, 'node_modules'));
            return {
                ecosystem: 'node',
                packageManager: pm,
                hasLockfile: hasLock,
                missingDependencies: nodeModulesExist ? [] : ['node_modules uninstalled'],
                isHealthy: nodeModulesExist,
                recommendedAction: nodeModulesExist ? undefined : `${pm} install`
            };
        }
        // 2. Python ecosystem
        if (fs.existsSync(path.join(workspaceRoot, 'pyproject.toml')) || fs.existsSync(path.join(workspaceRoot, 'requirements.txt'))) {
            const hasVenv = fs.existsSync(path.join(workspaceRoot, '.venv')) ||
                fs.existsSync(path.join(workspaceRoot, 'venv')) ||
                fs.existsSync(path.join(workspaceRoot, 'env'));
            return {
                ecosystem: 'python',
                packageManager: fs.existsSync(path.join(workspaceRoot, 'poetry.lock')) ? 'poetry' : 'pip',
                hasLockfile: fs.existsSync(path.join(workspaceRoot, 'poetry.lock')) || fs.existsSync(path.join(workspaceRoot, 'Pipfile.lock')),
                missingDependencies: hasVenv ? [] : ['Virtual environment not detected'],
                isHealthy: hasVenv,
                recommendedAction: hasVenv ? undefined : 'pip install -e .'
            };
        }
        // 3. Rust ecosystem
        if (fs.existsSync(path.join(workspaceRoot, 'Cargo.toml'))) {
            return {
                ecosystem: 'rust',
                packageManager: 'cargo',
                hasLockfile: fs.existsSync(path.join(workspaceRoot, 'Cargo.lock')),
                missingDependencies: [],
                isHealthy: true
            };
        }
        // 4. Go ecosystem
        if (fs.existsSync(path.join(workspaceRoot, 'go.mod'))) {
            return {
                ecosystem: 'go',
                packageManager: 'go',
                hasLockfile: fs.existsSync(path.join(workspaceRoot, 'go.sum')),
                missingDependencies: [],
                isHealthy: true
            };
        }
        return {
            ecosystem: 'unknown',
            packageManager: 'unknown',
            hasLockfile: false,
            missingDependencies: [],
            isHealthy: true
        };
    }
    /**
     * Perform controlled, safe environment repair in the VS Code terminal.
     */
    repairEnvironment(workspaceRoot) {
        const report = this.inspectEnvironment(workspaceRoot);
        if (report.ecosystem === 'node') {
            const cmd = report.packageManager === 'pnpm' ? 'pnpm install' :
                report.packageManager === 'yarn' ? 'yarn install' : 'npm install';
            this.executor.executeInTerminal(cmd, 'WIA: Repair Node Dependencies');
            return { success: true, message: `Running '${cmd}' in terminal to restore packages.` };
        }
        else if (report.ecosystem === 'python') {
            const isWin = process.platform === 'win32';
            let cmd = 'pip install -e .';
            if (!fs.existsSync(path.join(workspaceRoot, '.venv')) && !fs.existsSync(path.join(workspaceRoot, 'venv'))) {
                cmd = isWin
                    ? 'python -m venv .venv; .venv\\Scripts\\activate; pip install -e ".[dev]"'
                    : 'python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"';
            }
            this.executor.executeInTerminal(cmd, 'WIA: Repair Python Environment');
            return { success: true, message: 'Creating virtual environment and installing dependencies in terminal.' };
        }
        return { success: false, message: 'No repairable package ecosystem detected in workspace.' };
    }
}
exports.EnvironmentRepairEngine = EnvironmentRepairEngine;
//# sourceMappingURL=envRepair.js.map