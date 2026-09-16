"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const apiClient_1 = require("./apiClient");
const architectureProvider_1 = require("./providers/architectureProvider");
const symbolsProvider_1 = require("./providers/symbolsProvider");
const dependenciesProvider_1 = require("./providers/dependenciesProvider");
const WiaChatPanel_1 = require("./panels/WiaChatPanel");
let currentRepoId = null;
let currentRootPath = null;
function activate(context) {
    const apiClient = new apiClient_1.WiaApiClient();
    // Initialize Tree Providers
    const archProvider = new architectureProvider_1.ArchitectureTreeProvider(apiClient);
    const symbolsProvider = new symbolsProvider_1.SymbolsTreeProvider(apiClient);
    const depsProvider = new dependenciesProvider_1.DependenciesTreeProvider(apiClient);
    vscode.window.registerTreeDataProvider('wia-architecture', archProvider);
    vscode.window.registerTreeDataProvider('wia-symbols', symbolsProvider);
    vscode.window.registerTreeDataProvider('wia-dependencies', depsProvider);
    // Command: Scan Workspace
    const scanCmd = vscode.commands.registerCommand('wia.scanWorkspace', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showErrorMessage('No active workspace folder found to scan.');
            return;
        }
        const rootPath = workspaceFolders[0].uri.fsPath;
        currentRootPath = rootPath;
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'WIA: Ingesting & indexing workspace...',
            cancellable: false
        }, async (progress) => {
            try {
                const res = await apiClient.ingest(rootPath, workspaceFolders[0].name);
                currentRepoId = res.repo_id;
                // Poll status until complete
                let completed = false;
                for (let i = 0; i < 30; i++) {
                    await new Promise((r) => setTimeout(r, 1500));
                    const status = await apiClient.getStatus(currentRepoId);
                    if (status.status === 'completed') {
                        completed = true;
                        break;
                    }
                }
                archProvider.setRepository(currentRepoId, rootPath);
                symbolsProvider.setRepository(currentRepoId, rootPath);
                depsProvider.setRepository(currentRepoId);
                vscode.window.showInformationMessage(`✅ WIA: Workspace '${workspaceFolders[0].name}' indexed successfully!`);
            }
            catch (e) {
                vscode.window.showErrorMessage(`❌ WIA indexing failed: ${e.message}. Is the WIA engine running on port 8000?`);
            }
        });
    });
    // Command: Open AI Chat Panel
    const chatCmd = vscode.commands.registerCommand('wia.openChat', () => {
        WiaChatPanel_1.WiaChatPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });
    // Command: Explain Architecture
    const explainCmd = vscode.commands.registerCommand('wia.explainArchitecture', async () => {
        if (!currentRepoId) {
            vscode.window.showInformationMessage('Please run "WIA: Scan Workspace" first.');
            return;
        }
        WiaChatPanel_1.WiaChatPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });
    // Command: Trace Flow
    const flowCmd = vscode.commands.registerCommand('wia.traceFlow', async () => {
        if (!currentRepoId) {
            vscode.window.showInformationMessage('Please run "WIA: Scan Workspace" first.');
            return;
        }
        const editor = vscode.window.activeTextEditor;
        const selectedText = editor ? editor.document.getText(editor.selection).trim() : '';
        const entrySymbol = await vscode.window.showInputBox({
            prompt: 'Enter entry function name or API route to trace flow:',
            value: selectedText || 'main'
        });
        if (entrySymbol) {
            try {
                const res = await apiClient.traceFlow(currentRepoId, entrySymbol);
                vscode.window.showInformationMessage(`Traced ${res.flow?.length || 0} execution steps for '${entrySymbol}'`);
                WiaChatPanel_1.WiaChatPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
            }
            catch (e) {
                vscode.window.showErrorMessage(`Error tracing flow: ${e.message}`);
            }
        }
    });
    // Command: Analyze Impact
    const impactCmd = vscode.commands.registerCommand('wia.analyzeImpact', async () => {
        if (!currentRepoId) {
            vscode.window.showInformationMessage('Please run "WIA: Scan Workspace" first.');
            return;
        }
        const editor = vscode.window.activeTextEditor;
        const selectedText = editor ? editor.document.getText(editor.selection).trim() : '';
        const target = await vscode.window.showInputBox({
            prompt: 'Enter symbol name or file path to analyze impact for:',
            value: selectedText
        });
        if (target) {
            try {
                const res = await apiClient.analyzeImpact(currentRepoId, target);
                vscode.window.showInformationMessage(`Impact Analysis for '${target}': ${res.direct_impact_count} direct dependents, ${res.affected_files_count} files.`);
                WiaChatPanel_1.WiaChatPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
            }
            catch (e) {
                vscode.window.showErrorMessage(`Error analyzing impact: ${e.message}`);
            }
        }
    });
    // Command: Export OKF
    const okfCmd = vscode.commands.registerCommand('wia.exportOkf', async () => {
        if (!currentRepoId) {
            vscode.window.showInformationMessage('Please run "WIA: Scan Workspace" first.');
            return;
        }
        try {
            const res = await apiClient.exportOkf(currentRepoId);
            vscode.window.showInformationMessage(`✅ ${res.message || 'OKF Export generated at .wia/knowledge/'}`);
        }
        catch (e) {
            vscode.window.showErrorMessage(`Error generating OKF export: ${e.message}`);
        }
    });
    context.subscriptions.push(scanCmd, chatCmd, explainCmd, flowCmd, impactCmd, okfCmd);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map