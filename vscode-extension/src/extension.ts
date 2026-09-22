import * as vscode from 'vscode';
import { WiaApiClient } from './apiClient';
import { WiaSecretStorage } from './auth/secretStorage';
import { LayaDecisionEngine } from './decision/layaEngine';
import { WiaExecutor } from './executor/wiaExecutor';
import { EnvironmentRepairEngine } from './environment/envRepair';
import { WiaAgentPanel } from './panels/WiaAgentPanel';
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

    // Initialize Core Subsystems
    const secretStorage = new WiaSecretStorage(context.secrets, context.globalState);
    const layaEngine = new LayaDecisionEngine();
    const executor = new WiaExecutor(apiClient);
    const envRepair = new EnvironmentRepairEngine(executor);

    // Detect active workspace root
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders && workspaceFolders.length > 0) {
        currentRootPath = workspaceFolders[0].uri.fsPath;
    }

    // Initialize Tree Providers
    const archProvider = new ArchitectureTreeProvider(apiClient);
    const symbolsProvider = new SymbolsTreeProvider(apiClient);
    const depsProvider = new DependenciesTreeProvider(apiClient);

    vscode.window.registerTreeDataProvider('wia-architecture', archProvider);
    vscode.window.registerTreeDataProvider('wia-symbols', symbolsProvider);
    vscode.window.registerTreeDataProvider('wia-dependencies', depsProvider);

    // Initialize & Register CodeLens Provider
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
            statusBarItem.backgroundColor = undefined;
        } else {
            statusBarItem.text = '$(sparkle) WIA Agent';
            statusBarItem.tooltip = 'Click to open WIA Workspace Intelligence Agent';
            statusBarItem.backgroundColor = undefined;
        }
    };

    updateHealthStatus();
    vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('wia.apiBaseUrl')) {
            const newUrl = vscode.workspace.getConfiguration('wia').get<string>('apiBaseUrl', 'http://127.0.0.1:8000');
            apiClient.setBaseUrl(newUrl);
            updateHealthStatus();
        }
    });

    // PRIMARY COMMAND: Open Unified WIA Agent Panel
    const openAgentCmd = vscode.commands.registerCommand('wia.openAgent', () => {
        WiaAgentPanel.createOrShow(
            context.extensionUri,
            apiClient,
            secretStorage,
            layaEngine,
            executor,
            envRepair,
            currentRootPath,
            currentRepoId
        );
    });

    // Command: Scan Workspace
    const scanCmd = vscode.commands.registerCommand('wia.scanWorkspace', async () => {
        if (!currentRootPath && workspaceFolders && workspaceFolders.length > 0) {
            currentRootPath = workspaceFolders[0].uri.fsPath;
        }
        if (!currentRootPath) {
            vscode.window.showErrorMessage('No active workspace folder found to scan.');
            return;
        }

        vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'WIA: Ingesting & indexing workspace...',
                cancellable: false
            },
            async () => {
                try {
                    const res = await apiClient.ingest(currentRootPath!, workspaceFolders![0].name);
                    currentRepoId = res.repo_id;

                    archProvider.setRepository(currentRepoId, currentRootPath!);
                    symbolsProvider.setRepository(currentRepoId, currentRootPath!);
                    depsProvider.setRepository(currentRepoId);
                    codeLensProvider.setRepository(currentRepoId, currentRootPath!);

                    vscode.window.showInformationMessage(`✅ WIA: Workspace indexed successfully!`);
                } catch (e: any) {
                    // Fallback to local executor
                    await executor.executeOperation({ name: 'workspace.scan' }, currentRootPath!);
                    vscode.window.showInformationMessage(`✅ WIA: Local indexing completed!`);
                }
            }
        );
    });

    // Aliases & Tooling Commands
    const chatCmd = vscode.commands.registerCommand('wia.openChat', () => {
        vscode.commands.executeCommand('wia.openAgent');
    });

    const fixEnvCmd = vscode.commands.registerCommand('wia.fixEnvironment', () => {
        if (currentRootPath) {
            const res = envRepair.repairEnvironment(currentRootPath);
            vscode.window.showInformationMessage(res.message);
        }
    });

    const runProjectCmd = vscode.commands.registerCommand('wia.runProject', () => {
        if (currentRootPath) {
            executor.executeOperation({ name: 'project.run' }, currentRootPath);
        }
    });

    const runTestsCmd = vscode.commands.registerCommand('wia.runTests', () => {
        if (currentRootPath) {
            executor.executeOperation({ name: 'project.test' }, currentRootPath);
        }
    });

    const explainCmd = vscode.commands.registerCommand('wia.explainArchitecture', () => {
        WiaArchitecturePanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });

    const archPanelCmd = vscode.commands.registerCommand('wia.showArchitecturePanel', () => {
        WiaArchitecturePanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });

    const impactPanelCmd = vscode.commands.registerCommand('wia.showImpactPanel', () => {
        WiaImpactPanel.createOrShow(context.extensionUri, apiClient, currentRepoId, currentRootPath);
    });

    const refreshCmd = vscode.commands.registerCommand('wia.refreshViews', () => {
        archProvider.refresh();
        symbolsProvider.refresh();
        depsProvider.refresh();
        codeLensProvider.refresh();
        updateHealthStatus();
        vscode.window.showInformationMessage('WIA views refreshed.');
    });

    context.subscriptions.push(
        openAgentCmd,
        scanCmd,
        chatCmd,
        fixEnvCmd,
        runProjectCmd,
        runTestsCmd,
        explainCmd,
        archPanelCmd,
        impactPanelCmd,
        refreshCmd
    );
}

export function deactivate() {
    if (statusBarItem) {
        statusBarItem.dispose();
    }
}
