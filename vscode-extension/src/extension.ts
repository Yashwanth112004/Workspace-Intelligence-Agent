import * as vscode from 'vscode';
import { WiaApiClient } from './apiClient';
import { ArchitectureTreeProvider } from './providers/architectureProvider';
import { SymbolsTreeProvider } from './providers/symbolsProvider';
import { DependenciesTreeProvider } from './providers/dependenciesProvider';
import { WiaCodeLensProvider } from './providers/codeLensProvider';
import { WiaChatPanel } from './panels/WiaChatPanel';
import { WiaImpactPanel } from './panels/WiaImpactPanel';
import { WiaArchitecturePanel } from './panels/WiaArchitecturePanel';

let currentRepoId: string | null = null;
let currentRootPath: string | null = null;
let daemonTerminal: vscode.Terminal | null = null;
let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('wia');
    const baseUrl = config.get<string>('apiBaseUrl', 'http://127.0.0.1:8000');
    const apiClient = new WiaApiClient(baseUrl);

    // Initialize Tree Providers
    const archProvider = new ArchitectureTreeProvider(apiClient);
    const symbolsProvider = new SymbolsTreeProvider(apiClient);
    const depsProvider = new DependenciesTreeProvider(apiClient);

    vscode.window.registerTreeDataProvider('wia-architecture', archProvider);
    vscode.window.registerTreeDataProvider('wia-symbols', symbolsProvider);
    vscode.window.registerTreeDataProvider('wia-dependencies', depsProvider);

    // Initialize & Register CodeLens Provider for Multi-Language Support
    const codeLensProvider = new WiaCodeLensProvider(apiClient);
    const codeLensDisposable = vscode.languages.registerCodeLensProvider(
        [
            { scheme: 'file', language: 'python' },
            { scheme: 'file', language: 'typescript' },
            { scheme: 'file', language: 'javascript' },
            { scheme: 'file', language: 'go' },
            { scheme: 'file', language: 'rust' }
        ],
        codeLensProvider
    );
    context.subscriptions.push(codeLensDisposable);

    // Initialize Status Bar Item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'wia.checkHealthStatus';
    statusBarItem.text = '$(sync~spin) WIA';
    statusBarItem.tooltip = 'Checking WIA Engine Status...';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    const updateHealthStatus = async () => {
        const isOnline = await apiClient.checkHealth();
        if (isOnline) {
            statusBarItem.text = '$(zap) WIA: Online';
            statusBarItem.tooltip = `WIA Engine Daemon connected on ${apiClient.getBaseUrl()}`;
            statusBarItem.backgroundColor = undefined;
        } else {
            statusBarItem.text = '$(warning) WIA: Offline';
            statusBarItem.tooltip = 'WIA Engine Daemon offline. Click to start daemon.';
            statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
    };

    // Check health on startup and on configuration change
    updateHealthStatus();
    vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('wia.apiBaseUrl')) {
            const newUrl = vscode.workspace.getConfiguration('wia').get<string>('apiBaseUrl', 'http://127.0.0.1:8000');
            apiClient.setBaseUrl(newUrl);
            updateHealthStatus();
        }
    });

    // Command: Check / Toggle Health Status
    const healthCmd = vscode.commands.registerCommand('wia.checkHealthStatus', async () => {
        const isOnline = await apiClient.checkHealth();
        if (!isOnline) {
            const choice = await vscode.window.showWarningMessage(
                'WIA Engine Daemon is currently offline on ' + apiClient.getBaseUrl(),
                'Start Daemon',
                'Cancel'
            );
            if (choice === 'Start Daemon') {
                vscode.commands.executeCommand('wia.startDaemon');
            }
        } else {
            vscode.window.showInformationMessage(`✅ WIA Engine Daemon is online and healthy on ${apiClient.getBaseUrl()}`);
        }
    });

    // Command: Scan Workspace
    const scanCmd = vscode.commands.registerCommand('wia.scanWorkspace', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showErrorMessage('No active workspace folder found to scan.');
            return;
        }

        const rootPath = workspaceFolders[0].uri.fsPath;
        currentRootPath = rootPath;

        vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'WIA: Ingesting & indexing workspace...',
                cancellable: false
            },
            async () => {
                try {
                    const res = await apiClient.ingest(rootPath, workspaceFolders[0].name);
                    currentRepoId = res.repo_id;

                    // Poll status until complete or timeout
                    for (let i = 0; i < 40; i++) {
                        await new Promise((r) => setTimeout(r, 1500));
                        const status = await apiClient.getStatus(currentRepoId);
                        if (status.status === 'completed') {
                            break;
                        }
                    }

                    archProvider.setRepository(currentRepoId, rootPath);
                    symbolsProvider.setRepository(currentRepoId, rootPath);
                    depsProvider.setRepository(currentRepoId);
                    codeLensProvider.setRepository(currentRepoId, rootPath);

                    if (WiaChatPanel.currentPanel) {
                        WiaChatPanel.currentPanel.setRepository(currentRepoId, rootPath);
                    }

                    await updateHealthStatus();
                    vscode.window.showInformationMessage(`✅ WIA: Workspace '${workspaceFolders[0].name}' indexed successfully!`);
                } catch (e: any) {
                    vscode.window.showErrorMessage(`❌ WIA indexing failed: ${e.message}. Is the WIA daemon running on port 8000?`);
                }
            }
        );
    });

    // Command: Open AI Chat Panel
    const chatCmd = vscode.commands.registerCommand('wia.openChat', () => {
        WiaChatPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });

    // Command: Explain Architecture / Show Architecture Panel
    const explainCmd = vscode.commands.registerCommand('wia.explainArchitecture', () => {
        WiaArchitecturePanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });

    const archPanelCmd = vscode.commands.registerCommand('wia.showArchitecturePanel', () => {
        WiaArchitecturePanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });

    // Command: Trace Flow
    const flowCmd = vscode.commands.registerCommand('wia.traceFlow', async () => {
        const editor = vscode.window.activeTextEditor;
        const selectedText = editor ? editor.document.getText(editor.selection).trim() : '';

        const entrySymbol = await vscode.window.showInputBox({
            prompt: 'Enter entry function name or API route to trace flow:',
            value: selectedText || 'main'
        });

        if (entrySymbol) {
            vscode.commands.executeCommand('wia.traceFlowForSymbol', entrySymbol);
        }
    });

    // Command: Trace Flow for specific symbol (used by CodeLens)
    const traceFlowSymbolCmd = vscode.commands.registerCommand('wia.traceFlowForSymbol', async (symbolName: string) => {
        if (!currentRepoId) {
            const choice = await vscode.window.showInformationMessage(
                'Please run "WIA: Scan Workspace" first to build the knowledge graph.',
                'Scan Workspace'
            );
            if (choice === 'Scan Workspace') {
                vscode.commands.executeCommand('wia.scanWorkspace');
            }
            return;
        }

        try {
            const res = await apiClient.traceFlow(currentRepoId, symbolName);
            const stepCount = res.flow?.length || 0;
            vscode.window.showInformationMessage(`Traced ${stepCount} execution steps for '${symbolName}'`);
            WiaChatPanel.createOrShow(
                context.extensionUri,
                apiClient,
                currentRepoId,
                currentRootPath,
                `Trace execution call flow starting from function '${symbolName}'`
            );
        } catch (e: any) {
            vscode.window.showErrorMessage(`Error tracing flow for '${symbolName}': ${e.message}`);
        }
    });

    // Command: Analyze Impact (Prompt or Selection)
    const impactCmd = vscode.commands.registerCommand('wia.analyzeImpact', async () => {
        const editor = vscode.window.activeTextEditor;
        const selectedText = editor ? editor.document.getText(editor.selection).trim() : '';

        const target = await vscode.window.showInputBox({
            prompt: 'Enter symbol name or file path to analyze refactoring change impact:',
            value: selectedText
        });

        if (target) {
            vscode.commands.executeCommand('wia.analyzeImpactForSymbol', target);
        }
    });

    // Command: Analyze Impact for specific symbol (used by CodeLens & Context Menus)
    const impactSymbolCmd = vscode.commands.registerCommand(
        'wia.analyzeImpactForSymbol',
        (symbolName: string, _filePath?: string, _line?: number) => {
            WiaImpactPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath, symbolName);
        }
    );

    const impactPanelCmd = vscode.commands.registerCommand('wia.showImpactPanel', () => {
        WiaImpactPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });

    // Command: Export OKF
    const okfCmd = vscode.commands.registerCommand('wia.exportOkf', async () => {
        if (!currentRepoId) {
            vscode.window.showInformationMessage('Please run "WIA: Scan Workspace" first.');
            return;
        }
        try {
            const res = await apiClient.exportOkf(currentRepoId);
            vscode.window.showInformationMessage(`✅ ${res.message || 'OKF Export generated successfully at .wia/knowledge/'}`);
        } catch (e: any) {
            vscode.window.showErrorMessage(`Error generating OKF export: ${e.message}`);
        }
    });

    // Command: Start Local Intelligence Daemon
    const startDaemonCmd = vscode.commands.registerCommand('wia.startDaemon', () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        const cwd = workspaceFolders && workspaceFolders.length > 0 ? workspaceFolders[0].uri.fsPath : undefined;

        if (!daemonTerminal || daemonTerminal.exitStatus !== undefined) {
            daemonTerminal = vscode.window.createTerminal({
                name: 'WIA Intelligence Daemon',
                cwd: cwd
            });
        }
        daemonTerminal.show();
        daemonTerminal.sendText('python run_dev.py');
        vscode.window.showInformationMessage('🚀 Starting WIA Local Intelligence Engine Daemon (http://127.0.0.1:8000)...');

        // Poll health status
        setTimeout(() => updateHealthStatus(), 4000);
        setTimeout(() => updateHealthStatus(), 8000);
    });

    // Command: Refresh Knowledge Views
    const refreshCmd = vscode.commands.registerCommand('wia.refreshViews', () => {
        archProvider.refresh();
        symbolsProvider.refresh();
        depsProvider.refresh();
        codeLensProvider.refresh();
        updateHealthStatus();
        vscode.window.showInformationMessage('WIA views refreshed.');
    });

    context.subscriptions.push(
        scanCmd,
        chatCmd,
        explainCmd,
        archPanelCmd,
        flowCmd,
        traceFlowSymbolCmd,
        impactCmd,
        impactSymbolCmd,
        impactPanelCmd,
        okfCmd,
        startDaemonCmd,
        refreshCmd,
        healthCmd
    );
}

export function deactivate() {
    if (statusBarItem) {
        statusBarItem.dispose();
    }
}
