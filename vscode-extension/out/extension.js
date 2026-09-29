"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
const apiClient_1 = require("./apiClient");
const secretStorage_1 = require("./auth/secretStorage");
const layaEngine_1 = require("./decision/layaEngine");
const wiaExecutor_1 = require("./executor/wiaExecutor");
const envRepair_1 = require("./environment/envRepair");
const architectureProvider_1 = require("./providers/architectureProvider");
const symbolsProvider_1 = require("./providers/symbolsProvider");
const dependenciesProvider_1 = require("./providers/dependenciesProvider");
const codeLensProvider_1 = require("./providers/codeLensProvider");
const WiaImpactPanel_1 = require("./panels/WiaImpactPanel");
const WiaArchitecturePanel_1 = require("./panels/WiaArchitecturePanel");
const agentViewProvider_1 = require("./providers/agentViewProvider");
let currentRepoId = null;
let currentRootPath = null;
let daemonTerminal = null;
let statusBarItem;
function activate(context) {
    const config = vscode.workspace.getConfiguration('wia');
    const baseUrl = config.get('apiBaseUrl', 'http://127.0.0.1:8000');
    const apiClient = new apiClient_1.WiaApiClient(baseUrl);
    // Initialize Core Subsystems
    const secretStorage = new secretStorage_1.WiaSecretStorage(context.secrets, context.globalState);
    const layaEngine = new layaEngine_1.LayaDecisionEngine();
    const executor = new wiaExecutor_1.WiaExecutor(apiClient);
    const envRepair = new envRepair_1.EnvironmentRepairEngine(executor);
    // Detect active workspace root
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders && workspaceFolders.length > 0) {
        currentRootPath = workspaceFolders[0].uri.fsPath;
    }
    // Register WIA Agent Webview View Provider (Sidebar Interactive Agent & Chat)
    const agentViewProvider = new agentViewProvider_1.WiaAgentViewProvider(context.extensionUri, apiClient, secretStorage, layaEngine, executor, envRepair, currentRootPath);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('wia-agent-view', agentViewProvider, {
        webviewOptions: {
            retainContextWhenHidden: true
        }
    }));
    // Initialize Tree Providers with immediate workspace detection
    const archProvider = new architectureProvider_1.ArchitectureTreeProvider(apiClient);
    const symbolsProvider = new symbolsProvider_1.SymbolsTreeProvider(apiClient);
    const depsProvider = new dependenciesProvider_1.DependenciesTreeProvider(apiClient);
    if (currentRootPath) {
        archProvider.setRepository(null, currentRootPath);
        symbolsProvider.setRepository(null, currentRootPath);
        depsProvider.setRepository(null, currentRootPath);
    }
    vscode.window.registerTreeDataProvider('wia-architecture', archProvider);
    vscode.window.registerTreeDataProvider('wia-symbols', symbolsProvider);
    vscode.window.registerTreeDataProvider('wia-dependencies', depsProvider);
    // Initialize & Register CodeLens Provider
    const codeLensProvider = new codeLensProvider_1.WiaCodeLensProvider(apiClient);
    if (currentRootPath) {
        codeLensProvider.setRepository(null, currentRootPath);
    }
    const codeLensDisposable = vscode.languages.registerCodeLensProvider([
        { scheme: 'file', language: 'python' },
        { scheme: 'file', language: 'typescript' },
        { scheme: 'file', language: 'javascript' },
        { scheme: 'file', language: 'go' },
        { scheme: 'file', language: 'rust' }
    ], codeLensProvider);
    context.subscriptions.push(codeLensDisposable);
    // Initialize Status Bar Item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'wia.openAgent';
    statusBarItem.text = '$(zap) WIA Agent';
    statusBarItem.tooltip = 'Click to open WIA Workspace Intelligence Agent';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
    const updateHealthStatus = async () => {
        const isOnline = await apiClient.checkHealth();
        if (isOnline) {
            statusBarItem.text = '$(zap) WIA: Online';
            statusBarItem.tooltip = `WIA Engine Daemon connected on ${apiClient.getBaseUrl()}`;
        }
        else {
            statusBarItem.text = '$(zap) WIA Agent';
            statusBarItem.tooltip = 'Click to open WIA Workspace Intelligence Agent';
        }
    };
    updateHealthStatus();
    vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('wia.apiBaseUrl')) {
            const newUrl = vscode.workspace.getConfiguration('wia').get('apiBaseUrl', 'http://127.0.0.1:8000');
            apiClient.setBaseUrl(newUrl);
            updateHealthStatus();
        }
    });
    // Listen for workspace folder changes
    vscode.workspace.onDidChangeWorkspaceFolders(async () => {
        const folders = vscode.workspace.workspaceFolders;
        if (folders && folders.length > 0) {
            currentRootPath = folders[0].uri.fsPath;
            await agentViewProvider.setWorkspaceRoot(currentRootPath);
            archProvider.setRepository(currentRepoId, currentRootPath);
            symbolsProvider.setRepository(currentRepoId, currentRootPath);
            depsProvider.setRepository(currentRepoId, currentRootPath);
            codeLensProvider.setRepository(currentRepoId, currentRootPath);
            agentViewProvider.setWorkspaceRoot(currentRootPath);
        }
    });
    const getActiveSymbolOrPrompt = async (promptTitle) => {
        const editor = vscode.window.activeTextEditor;
        let candidate;
        if (editor && editor.document) {
            const selection = editor.selection;
            if (!selection.isEmpty) {
                candidate = editor.document.getText(selection).trim();
            }
            else {
                const range = editor.document.getWordRangeAtPosition(selection.active);
                if (range) {
                    candidate = editor.document.getText(range).trim();
                }
            }
        }
        return await vscode.window.showInputBox({
            prompt: promptTitle,
            value: candidate || ''
        });
    };
    // ==========================================
    // ALL CANONICAL COMMAND REGISTRATIONS
    // ==========================================
    // 1. Primary: Open Agent View
    const openAgentCmd = vscode.commands.registerCommand('wia.openAgent', async () => {
        await vscode.commands.executeCommand('workbench.view.extension.wia-container');
        await vscode.commands.executeCommand('wia-agent-view.focus');
    });
    // 2. Open Chat Alias
    const openChatCmd = vscode.commands.registerCommand('wia.openChat', () => {
        vscode.commands.executeCommand('wia.openAgent');
    });
    // 3. Scan & Ingest Workspace
    const scanCmd = vscode.commands.registerCommand('wia.scanWorkspace', async () => {
        if (!currentRootPath && workspaceFolders && workspaceFolders.length > 0) {
            currentRootPath = workspaceFolders[0].uri.fsPath;
        }
        if (!currentRootPath) {
            vscode.window.showErrorMessage('No active workspace folder found to scan.');
            return;
        }
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'WIA: Ingesting & indexing workspace...',
            cancellable: false
        }, async () => {
            try {
                const res = await apiClient.ingest(currentRootPath, workspaceFolders[0].name);
                currentRepoId = res.repo_id;
                archProvider.setRepository(currentRepoId, currentRootPath);
                symbolsProvider.setRepository(currentRepoId, currentRootPath);
                depsProvider.setRepository(currentRepoId, currentRootPath);
                codeLensProvider.setRepository(currentRepoId, currentRootPath);
                vscode.window.showInformationMessage(`✅ WIA: Workspace indexed successfully!`);
            }
            catch (e) {
                // Fallback to local executor
                await executor.executeWiaCommand('index', {}, currentRootPath);
                archProvider.setRepository(null, currentRootPath);
                symbolsProvider.setRepository(null, currentRootPath);
                depsProvider.setRepository(null, currentRootPath);
                codeLensProvider.setRepository(null, currentRootPath);
                vscode.window.showInformationMessage(`✅ WIA: Local indexing completed!`);
            }
        });
    });
    // 4. Architecture Map & Panels
    const archCmd = vscode.commands.registerCommand('wia.architecture', () => {
        WiaArchitecturePanel_1.WiaArchitecturePanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath, executor);
    });
    const showArchPanelCmd = vscode.commands.registerCommand('wia.showArchitecturePanel', () => {
        WiaArchitecturePanel_1.WiaArchitecturePanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath, executor);
    });
    const explainArchCmd = vscode.commands.registerCommand('wia.explainArchitecture', () => {
        WiaArchitecturePanel_1.WiaArchitecturePanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath, executor);
    });
    // 5. Dependencies Analysis & Resolution
    const depsCmd = vscode.commands.registerCommand('wia.deps', async () => {
        if (!currentRootPath)
            return;
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'WIA: Analyzing dependencies...' }, async () => {
            const res = await executor.executeWiaCommand('deps', {}, currentRootPath);
            if (res.stdout) {
                const channel = vscode.window.createOutputChannel('WIA Dependencies');
                channel.clear();
                channel.appendLine(res.stdout);
                channel.show();
            }
            const envReport = envRepair.inspectEnvironment(currentRootPath);
            if (envReport.missingDependencies.length > 0) {
                vscode.window.showWarningMessage(`⚠️ WIA: Detected ${envReport.missingDependencies.length} missing dependencies.`, 'Repair Environment').then(action => {
                    if (action === 'Repair Environment') {
                        vscode.commands.executeCommand('wia.fixEnvironment');
                    }
                });
            }
            else {
                vscode.window.showInformationMessage('✅ WIA: Package dependencies verified.');
            }
        });
    });
    // 6. Workspace Status
    const statusCmd = vscode.commands.registerCommand('wia.status', async () => {
        if (!currentRootPath)
            return;
        const res = await executor.executeWiaCommand('status', {}, currentRootPath);
        vscode.window.showInformationMessage(res.stdout || 'WIA workspace index is active and up to date.');
    });
    // 7. Diagnostics (Doctor)
    const doctorCmd = vscode.commands.registerCommand('wia.doctor', async () => {
        if (!currentRootPath)
            return;
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'WIA: Running environment diagnostics...' }, async () => {
            const res = await executor.executeWiaCommand('doctor', {}, currentRootPath);
            const channel = vscode.window.createOutputChannel('WIA Diagnostics');
            channel.clear();
            channel.appendLine(res.stdout || res.stderr);
            channel.show();
        });
    });
    // 8. Fix Environment
    const fixEnvCmd = vscode.commands.registerCommand('wia.fixEnvironment', () => {
        if (currentRootPath) {
            const res = envRepair.repairEnvironment(currentRootPath);
            vscode.window.showInformationMessage(res.message);
        }
    });
    // 9. Summary Generator
    const summaryCmd = vscode.commands.registerCommand('wia.summary', async () => {
        if (!currentRootPath)
            return;
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'WIA: Generating codebase summary...' }, async () => {
            const res = await executor.executeWiaCommand('summary', {}, currentRootPath);
            const doc = await vscode.workspace.openTextDocument({
                content: res.stdout || '# Codebase Summary\n\nNo summary available.',
                language: 'markdown'
            });
            vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
        });
    });
    // 10. List Indexed Files
    const filesCmd = vscode.commands.registerCommand('wia.files', async () => {
        if (!currentRootPath)
            return;
        const res = await executor.executeWiaCommand('files', { limit: 100 }, currentRootPath);
        const lines = (res.stdout || '').split('\n').filter(l => l.trim().length > 0);
        const items = lines.map(l => ({ label: l.replace(/^[-*]\s*/, ''), description: 'Indexed File' }));
        const pick = await vscode.window.showQuickPick(items, { placeHolder: 'Select an indexed file to open' });
        if (pick && pick.label) {
            const fullPath = path.join(currentRootPath, pick.label);
            if (fs.existsSync(fullPath)) {
                vscode.window.showTextDocument(vscode.Uri.file(fullPath));
            }
        }
    });
    // 11. Tech Stack Info
    const infoCmd = vscode.commands.registerCommand('wia.info', async () => {
        if (!currentRootPath)
            return;
        const res = await executor.executeWiaCommand('info', {}, currentRootPath);
        vscode.window.showInformationMessage(res.stdout || 'No tech stack info returned.');
    });
    // 12. Search Symbols & Files
    const searchCmd = vscode.commands.registerCommand('wia.search', async () => {
        if (!currentRootPath)
            return;
        const query = await getActiveSymbolOrPrompt('Enter symbol name, function, class, or keyword to search:');
        if (!query)
            return;
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: `WIA: Searching for '${query}'...` }, async () => {
            const res = await executor.executeWiaCommand('search', { query }, currentRootPath);
            const channel = vscode.window.createOutputChannel('WIA Symbol Search');
            channel.clear();
            channel.appendLine(res.stdout || `No symbols found for '${query}'.`);
            channel.show();
        });
    });
    // 13. Explain Symbol / Component
    const explainSymbolCmd = vscode.commands.registerCommand('wia.explainSymbol', async () => {
        if (!currentRootPath)
            return;
        const target = await getActiveSymbolOrPrompt('Enter symbol or file to explain:');
        if (!target)
            return;
        await vscode.commands.executeCommand('wia.openAgent');
    });
    // 14. Impact Analysis Panel & CodeLens Handlers
    const impactCmd = vscode.commands.registerCommand('wia.impact', async () => {
        const symbol = await getActiveSymbolOrPrompt('Enter symbol identifier to evaluate refactoring impact:');
        WiaImpactPanel_1.WiaImpactPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath, symbol, executor);
    });
    const showImpactPanelCmd = vscode.commands.registerCommand('wia.showImpactPanel', () => {
        WiaImpactPanel_1.WiaImpactPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath, undefined, executor);
    });
    const analyzeImpactForSymbolCmd = vscode.commands.registerCommand('wia.analyzeImpactForSymbol', (symbolName) => {
        WiaImpactPanel_1.WiaImpactPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath, symbolName, executor);
    });
    // 15. Flow Trace & CodeLens Handlers
    const flowCmd = vscode.commands.registerCommand('wia.flow', async () => {
        if (!currentRootPath)
            return;
        const entry = await getActiveSymbolOrPrompt('Enter entry point symbol or function to trace:');
        if (!entry)
            return;
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: `WIA: Tracing call flow for '${entry}'...` }, async () => {
            const res = await executor.executeWiaCommand('flow', { entry }, currentRootPath);
            const channel = vscode.window.createOutputChannel('WIA Call Flow');
            channel.clear();
            channel.appendLine(res.stdout || `Call flow for '${entry}':\n${res.stderr}`);
            channel.show();
        });
    });
    const traceFlowForSymbolCmd = vscode.commands.registerCommand('wia.traceFlowForSymbol', async (symbolName) => {
        if (!currentRootPath)
            return;
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: `WIA: Tracing call hierarchy for '${symbolName}'...` }, async () => {
            const res = await executor.executeWiaCommand('flow', { entry: symbolName }, currentRootPath);
            const channel = vscode.window.createOutputChannel('WIA Call Flow');
            channel.clear();
            channel.appendLine(`=== Call Hierarchy & Flow for '${symbolName}' ===\n\n` + (res.stdout || res.stderr));
            channel.show();
        });
    });
    // 16. Git Diff Impact & Hotspots
    const diffCmd = vscode.commands.registerCommand('wia.diff', async () => {
        if (!currentRootPath)
            return;
        const res = await executor.executeWiaCommand('diff', {}, currentRootPath);
        const channel = vscode.window.createOutputChannel('WIA Git Diff Impact');
        channel.clear();
        channel.appendLine(res.stdout || res.stderr);
        channel.show();
    });
    const gitHotspotsCmd = vscode.commands.registerCommand('wia.gitHotspots', async () => {
        if (!currentRootPath)
            return;
        const res = await executor.executeWiaCommand('git', {}, currentRootPath);
        const channel = vscode.window.createOutputChannel('WIA Git Hotspots');
        channel.clear();
        channel.appendLine(res.stdout || res.stderr);
        channel.show();
    });
    // 17. Security & Secret Scan
    const securityScanCmd = vscode.commands.registerCommand('wia.securityScan', async () => {
        if (!currentRootPath)
            return;
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'WIA: Scanning workspace for secrets & security risks...' }, async () => {
            const res = await executor.executeWiaCommand('security', {}, currentRootPath);
            const channel = vscode.window.createOutputChannel('WIA Security Scan');
            channel.clear();
            channel.appendLine(res.stdout || res.stderr);
            channel.show();
        });
    });
    // 18. Standalone HTML Report Generator
    const generateReportCmd = vscode.commands.registerCommand('wia.generateReport', async () => {
        if (!currentRootPath)
            return;
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'WIA: Generating interactive HTML intelligence report...' }, async () => {
            const res = await executor.executeWiaCommand('report', {}, currentRootPath);
            vscode.window.showInformationMessage('✅ WIA: HTML Report generated successfully!', 'Open Report').then(action => {
                if (action === 'Open Report') {
                    const reportPath = path.join(currentRootPath, 'wia-report.html');
                    if (fs.existsSync(reportPath)) {
                        vscode.env.openExternal(vscode.Uri.file(reportPath));
                    }
                }
            });
        });
    });
    // 19. Project Run, Test, and Build
    const runProjectCmd = vscode.commands.registerCommand('wia.runProject', () => {
        if (currentRootPath) {
            executor.executeWiaCommand('run', {}, currentRootPath);
        }
    });
    const runTestsCmd = vscode.commands.registerCommand('wia.runTests', () => {
        if (currentRootPath) {
            executor.executeWiaCommand('test', {}, currentRootPath);
        }
    });
    const buildProjectCmd = vscode.commands.registerCommand('wia.buildProject', () => {
        if (currentRootPath) {
            executor.executeWiaCommand('build', {}, currentRootPath);
        }
    });
    // 20. AI Configuration & Settings
    const configCmd = vscode.commands.registerCommand('wia.config', async () => {
        const providers = ['openrouter', 'nvidia', 'openai', 'anthropic', 'gemini', 'local'];
        const selected = (await vscode.window.showQuickPick(providers, {
            placeHolder: 'Select AI Provider for Workspace Intelligence Agent'
        }));
        if (selected) {
            const defaultModel = secretStorage_1.DEFAULT_PROVIDER_MODELS[selected];
            const model = await vscode.window.showInputBox({
                prompt: `Enter model name for ${selected}`,
                value: defaultModel
            });
            if (model) {
                if (selected !== 'local') {
                    const key = await vscode.window.showInputBox({
                        prompt: `Enter API Key for ${selected}`,
                        password: true
                    });
                    await secretStorage.setActiveProviderConfig(selected, model, key || undefined);
                }
                else {
                    await secretStorage.setActiveProviderConfig(selected, model);
                }
                vscode.window.showInformationMessage(`WIA configuration updated: ${selected} (${model})`);
            }
        }
    });
    // 21. Refresh Views
    const refreshCmd = vscode.commands.registerCommand('wia.refreshViews', () => {
        archProvider.refresh();
        symbolsProvider.refresh();
        depsProvider.refresh();
        codeLensProvider.refresh();
        updateHealthStatus();
        vscode.window.showInformationMessage('WIA views refreshed.');
    });
    // 22. Start Daemon
    const startDaemonCmd = vscode.commands.registerCommand('wia.startDaemon', () => {
        if (daemonTerminal) {
            daemonTerminal.dispose();
        }
        daemonTerminal = vscode.window.createTerminal({
            name: 'WIA Daemon',
            cwd: currentRootPath || undefined
        });
        daemonTerminal.show();
        daemonTerminal.sendText('python -m wia daemon');
        vscode.window.showInformationMessage('WIA: Starting Engine Daemon on port 8000...');
        setTimeout(() => updateHealthStatus(), 3000);
    });
    context.subscriptions.push(openAgentCmd, openChatCmd, scanCmd, archCmd, showArchPanelCmd, explainArchCmd, depsCmd, statusCmd, doctorCmd, fixEnvCmd, summaryCmd, filesCmd, infoCmd, searchCmd, explainSymbolCmd, impactCmd, showImpactPanelCmd, analyzeImpactForSymbolCmd, flowCmd, traceFlowForSymbolCmd, diffCmd, gitHotspotsCmd, securityScanCmd, generateReportCmd, runProjectCmd, runTestsCmd, buildProjectCmd, configCmd, refreshCmd, startDaemonCmd);
}
function deactivate() {
    if (statusBarItem) {
        statusBarItem.dispose();
    }
    if (daemonTerminal) {
        daemonTerminal.dispose();
    }
}
//# sourceMappingURL=extension.js.map