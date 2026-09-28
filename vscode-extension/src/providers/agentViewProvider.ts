/**
 * Canonical WIA Agent WebviewView Provider for VS Code & Antigravity IDE.
 *
 * Implements:
 * 1. State-Driven Lifecycle:
 *    - Onboarding: AI Provider & API Key Setup (stored in SecretStorage)
 *    - Authorization: One-time workspace permission
 *    - Initial Analysis: Deterministic safe WIA information-gathering orchestration
 *    - Ready Dashboard & Conversational Agent
 * 2. Pure Natural-Language Interface (NO slash-command chips, NO debug routing strings)
 * 3. Exact Query Pipeline:
 *    - Query -> Laya Decision -> Matched WIA Command -> Real WIA CLI Execution -> Structured UI
 *    - Query -> Laya Decision -> No Match -> WIA Retrieval Context -> LLM Reasoning -> AI Answer
 * 4. Dedicated Sections:
 *    - Architecture: Real WIA ArchitectureAnalyzer output
 *    - Dependencies: Real WIA ManifestParser & ConflictDetector output
 *    - Environment: Real WIA Doctor diagnostic health output
 *    - Commands: Detected project execution commands
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { WiaApiClient } from '../apiClient';
import { WiaSecretStorage, AIProviderName, DEFAULT_PROVIDER_MODELS } from '../auth/secretStorage';
import { LayaDecisionEngine, EditorContext } from '../decision/layaEngine';
import { WiaExecutor, WorkspaceIntelligence } from '../executor/wiaExecutor';
import { EnvironmentRepairEngine } from '../environment/envRepair';
import { WiaLLMClient } from '../llm/llmClient';
import { CANONICAL_WIA_COMMAND_REGISTRY } from '../registry/wiaCommandRegistry';

function escapeHtml(text: any): string {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

export class WiaAgentViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'wia-agent-view';
    private _view?: vscode.WebviewView;
    private workspaceIntelligence: WorkspaceIntelligence | null = null;
    private isAnalyzing: boolean = false;
    private llmClient: WiaLLMClient;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly apiClient: WiaApiClient,
        private readonly secretStorage: WiaSecretStorage,
        private readonly layaEngine: LayaDecisionEngine,
        private readonly executor: WiaExecutor,
        private readonly envRepair: EnvironmentRepairEngine,
        private currentRootPath: string | null
    ) {
        this.llmClient = new WiaLLMClient();
    }

    public getRootPath(): string | null {
        if (this.currentRootPath) return this.currentRootPath;
        const folders = vscode.workspace.workspaceFolders;
        if (folders && folders.length > 0) {
            this.currentRootPath = folders[0].uri.fsPath;
            return this.currentRootPath;
        }
        return null;
    }

    public async resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        // Attach message listener immediately to never drop incoming events
        webviewView.webview.onDidReceiveMessage(async (data) => {
            if (!data) return;
            switch (data.type) {
                case 'testConnection':
                    await this.handleTestConnection(data.provider, data.apiKey);
                    break;
                case 'saveAiConfig':
                    await this.handleSaveAiConfig(data.provider, data.model, data.apiKey);
                    break;
                case 'authorizeWorkspace':
                    await this.handleAuthorizeWorkspace();
                    break;
                case 'openSettings':
                    await this.showSettingsModal();
                    break;
                case 'reIndex':
                    await this.startFullAnalysis();
                    break;
                case 'askAgent':
                    await this.handleQuery(data.query);
                    break;
                case 'runCommand':
                    this.executor.executeInTerminal(data.command, data.name || 'WIA Command');
                    break;
                case 'authorizeRepair': {
                    const root = this.getRootPath();
                    if (root) {
                        const cmd = data.command;
                        this.executor.executeInTerminal(cmd, 'WIA: Dependency Resolution');
                        vscode.window.showInformationMessage(`WIA: Executing dependency resolution: ${cmd}`);
                        this._view?.webview.postMessage({
                            type: 'repairStarted',
                            command: cmd
                        });
                    }
                    break;
                }
                case 'openFile':
                    this.handleOpenFile(data.filePath, data.line);
                    break;
                case 'triggerTab':
                    if (data.tab) {
                        await this.handleTabTrigger(data.tab);
                    }
                    break;
            }
        });

        await this.renderCurrentState();
    }

    public async setWorkspaceRoot(rootPath: string | null) {
        this.currentRootPath = rootPath;
        this.workspaceIntelligence = null;
        await this.renderCurrentState();
    }

    private async renderCurrentState() {
        if (!this._view) return;

        const root = this.getRootPath();
        if (!root) {
            this._view.webview.html = this.getHtmlForNoWorkspace();
            return;
        }

        const hasConfig = await this.secretStorage.hasValidLLMConfiguration();
        if (!hasConfig) {
            this._view.webview.html = this.getHtmlForOnboarding();
            return;
        }

        const isAuth = this.secretStorage.isWorkspaceAuthorized(root);
        if (!isAuth) {
            this._view.webview.html = this.getHtmlForAuthorization();
            return;
        }

        if (!this.workspaceIntelligence && !this.isAnalyzing) {
            this._view.webview.html = this.getHtmlForAnalysisProgress();
            this.startFullAnalysis();
            return;
        }

        this._view.webview.html = this.getHtmlForDashboard();
    }

    private async handleTestConnection(provider: AIProviderName, apiKey?: string) {
        if (!this._view) return;
        this._view.webview.postMessage({ type: 'testStatus', status: 'testing', message: 'Testing connection to provider...' });

        if (provider === 'local') {
            this._view.webview.postMessage({ type: 'testStatus', status: 'success', message: 'Offline deterministic engine is active and ready.' });
            return;
        }

        const key = apiKey || await this.secretStorage.getApiKey(provider);
        if (!key) {
            this._view.webview.postMessage({ type: 'testStatus', status: 'error', message: `No API key provided for ${provider}.` });
            return;
        }

        const defaultModel = DEFAULT_PROVIDER_MODELS[provider] || 'anthropic/claude-3.5-sonnet';
        const testRes = await this.llmClient.testProviderConnection({
            provider,
            model: defaultModel,
            apiKey: key
        });

        this._view.webview.postMessage({
            type: 'testStatus',
            status: testRes.success ? 'success' : 'error',
            message: testRes.message
        });
    }

    private async handleSaveAiConfig(provider: AIProviderName, model: string, apiKey?: string) {
        await this.secretStorage.setActiveProviderConfig(provider, model, apiKey);
        vscode.window.showInformationMessage(`WIA: AI provider configured as '${provider}' (${model}).`);
        await this.renderCurrentState();
    }

    private async handleAuthorizeWorkspace() {
        const root = this.getRootPath();
        if (!root) return;
        await this.secretStorage.setWorkspaceAuthorized(root, true);
        await this.renderCurrentState();
    }

    private async showSettingsModal() {
        const config = await this.secretStorage.getActiveProviderConfig();
        const providers: AIProviderName[] = ['openrouter', 'nvidia', 'openai', 'anthropic', 'gemini', 'local'];
        
        const selected = await vscode.window.showQuickPick(providers, {
            placeHolder: `Current AI Provider: ${config.provider}`
        });

        if (selected) {
            const defaultModel = DEFAULT_PROVIDER_MODELS[selected as AIProviderName];
            const modelInput = await vscode.window.showInputBox({
                prompt: `Enter model name for ${selected}`,
                value: config.provider === selected ? config.model : defaultModel
            });

            if (modelInput) {
                if (selected !== 'local') {
                    const keyInput = await vscode.window.showInputBox({
                        prompt: `Enter API key for ${selected}`,
                        password: true,
                        value: config.provider === selected ? config.apiKey : undefined
                    });

                    await this.secretStorage.setActiveProviderConfig(selected as AIProviderName, modelInput, keyInput || undefined);
                } else {
                    await this.secretStorage.setActiveProviderConfig(selected as AIProviderName, modelInput);
                }
                vscode.window.showInformationMessage(`WIA configuration updated to ${selected} (${modelInput}).`);
                await this.renderCurrentState();
            }
        }
    }

    private async startFullAnalysis() {
        const root = this.getRootPath();
        if (!root || this.isAnalyzing) return;
        this.isAnalyzing = true;

        try {
            this.workspaceIntelligence = await this.executor.performComprehensiveInitialAnalysis(
                root,
                (step, percent) => {
                    this._view?.webview.postMessage({
                        type: 'analysisProgress',
                        step,
                        percent
                    });
                }
            );
        } catch (e: any) {
            vscode.window.showErrorMessage(`WIA Analysis: ${e.message}`);
        } finally {
            if (!this.workspaceIntelligence) {
                this.workspaceIntelligence = this.createFallbackWorkspaceIntelligence(root);
            }
            this.isAnalyzing = false;
            await this.renderCurrentState();
        }
    }

    private createFallbackWorkspaceIntelligence(root: string): WorkspaceIntelligence {
        const wsName = path.basename(root);
        return {
            project: {
                name: wsName,
                type: 'Workspace Project',
                primaryLanguage: 'Workspace',
                summaryText: `AI-Indexed Workspace: ${wsName}`
            },
            repository: {
                totalFiles: 0,
                indexedFiles: 0,
                entryPoints: [],
                importantDirectories: [],
                importantFiles: []
            },
            techStack: {
                languages: [],
                frameworks: [],
                libraries: [],
                tools: []
            },
            architecture: {
                subsystems: [
                    { name: 'Core Subsystems', role: 'Workspace Architecture Components', files: 0, symbols: 0, dependencies: [] }
                ]
            },
            dependencies: {
                total: 0,
                healthy: 0,
                missing: [],
                conflicts: [],
                outdated: [],
                hasLockfile: false
            },
            environment: {
                ecosystem: 'local',
                packageManager: 'system',
                isHealthy: true,
                issues: []
            },
            commands: this.executor.detectProjectCommands(root),
            codebase: {
                classes: 0,
                functions: 0,
                symbols: 0,
                languagesBreakdown: {}
            },
            health: {
                status: 'healthy',
                errors: [],
                warnings: [],
                info: []
            }
        };
    }

    private async handleTabTrigger(tab: string) {
        let query = '';
        if (tab === 'architecture') query = 'Architecture';
        else if (tab === 'dependencies') query = 'Check dependencies';
        else if (tab === 'environment') query = 'Check environment';
        else if (tab === 'status') query = 'Show project status';

        if (query) {
            await this.handleQuery(query);
        }
    }

    /**
     * Core Query Execution Pipeline:
     * User Natural Language -> Laya Decision -> WIA Command / AI Fallback -> Structured UI
     */
    private async handleQuery(query: string) {
        if (!query || !query.trim()) return;

        let root = this.getRootPath();
        if (!root) {
            const folders = vscode.workspace.workspaceFolders;
            if (folders && folders.length > 0) {
                root = folders[0].uri.fsPath;
                this.currentRootPath = root;
            } else if (vscode.window.activeTextEditor) {
                const docUri = vscode.window.activeTextEditor.document.uri;
                const folder = vscode.workspace.getWorkspaceFolder(docUri);
                if (folder) {
                    root = folder.uri.fsPath;
                    this.currentRootPath = root;
                } else if (docUri.scheme === 'file') {
                    root = path.dirname(docUri.fsPath);
                    this.currentRootPath = root;
                }
            }
        }

        if (!this._view) return;

        if (!root) {
            this._view.webview.postMessage({
                type: 'queryResult',
                query,
                content: '⚠️ **No Workspace Detected**: Please open a project folder in VS Code to run WIA queries.'
            });
            return;
        }

        try {
            // 1. Collect Editor Context
            const editor = vscode.window.activeTextEditor;
            const editorContext: EditorContext = {};
            if (editor && editor.document) {
                try {
                    editorContext.activeFilePath = path.relative(root, editor.document.uri.fsPath);
                } catch {
                    editorContext.activeFilePath = editor.document.uri.fsPath;
                }
                const selection = editor.selection;
                if (!selection.isEmpty) {
                    editorContext.selectedText = editor.document.getText(selection);
                }
            }

            this._view.webview.postMessage({ type: 'queryStarted', query });

            // 2. Laya Router Decision
            const decision = this.layaEngine.route(query, CANONICAL_WIA_COMMAND_REGISTRY, editorContext);

            // 3. Execution based on Laya Decision
            let responseContent = '';

            if (decision.route_type === 'wia_command' && decision.command) {
                this._view.webview.postMessage({
                    type: 'statusUpdate',
                    step: `Executing ${decision.command}...`
                });

                const result = await this.executor.executeWiaCommand(
                    decision.command,
                    decision.arguments,
                    root
                );

                if (result.status === 'completed' && result.stdout) {
                    responseContent = result.stdout;
                } else if (result.stderr) {
                    responseContent = `**WIA Command Error (${decision.command}):**\n\`\`\`\n${result.stderr}\n\`\`\``;
                } else if (result.stdout) {
                    responseContent = result.stdout;
                } else {
                    responseContent = `WIA command \`${decision.command}\` completed successfully.`;
                }

                // Interactive Dependency Notification & Resolution
                if (decision.command === 'deps') {
                    try {
                        const envReport = this.envRepair.inspectEnvironment(root);
                        const hasIssues = (result.stdout && (result.stdout.includes('⚠️') || 
                                          result.stdout.toLowerCase().includes('conflict') || 
                                          result.stdout.toLowerCase().includes('duplicate_entry'))) ||
                                          envReport.missingDependencies.length > 0;

                        if (hasIssues) {
                            const repairCmd = envReport.recommendedAction || 'pip install -e .';
                            vscode.window.showWarningMessage(
                                `⚠️ WIA: Dependency issues/conflicts detected in workspace. Would you like to resolve them?`,
                                'Resolve & Install',
                                'Dismiss'
                            ).then(selection => {
                                if (selection === 'Resolve & Install') {
                                    this.executor.executeInTerminal(repairCmd, 'WIA: Dependency Resolution', root!);
                                    vscode.window.showInformationMessage(`WIA: Executing '${repairCmd}' in terminal.`);
                                }
                            });
                        } else {
                            vscode.window.showInformationMessage('✅ WIA: All workspace dependencies are satisfied and verified!');
                        }
                    } catch (envErr) {
                        console.error('Environment check error:', envErr);
                    }
                }
            } else {
                // AI Fallback Layer: Run grounded reasoning
                this._view.webview.postMessage({
                    type: 'statusUpdate',
                    step: 'Reasoning over codebase context with AI...'
                });

                const activeConfig = await this.secretStorage.getActiveProviderConfig();
                let groundedContext = '';
                try {
                    groundedContext = await this.executor.retrieveRelevantContext(
                        query,
                        root,
                        editorContext
                    );
                } catch {
                    groundedContext = `Repository: ${path.basename(root)}`;
                }

                if (activeConfig.apiKey && activeConfig.provider !== 'local') {
                    try {
                        responseContent = await this.llmClient.answerWithContext(
                            query,
                            groundedContext,
                            activeConfig
                        );
                    } catch (err: any) {
                        responseContent = `### Workspace Intelligence\n\n> ⚠️ **AI Provider (${activeConfig.provider.toUpperCase()}) Notice:** ${err.message}\n\n*Displaying grounded local indexed repository context:*\n\n${groundedContext}`;
                    }
                } else {
                    const askResult = await this.executor.executeWiaCommand('ask', { query }, root);
                    if (askResult.status === 'completed' && askResult.stdout && !askResult.stdout.includes('Error')) {
                        responseContent = askResult.stdout;
                    } else {
                        responseContent = `### Local Workspace Intelligence\n\n${groundedContext}`;
                    }
                }
            }

            let envReport;
            try {
                envReport = this.envRepair.inspectEnvironment(root);
            } catch {
                envReport = undefined;
            }

            let commands: any = {};
            try {
                commands = this.executor.detectProjectCommands(root);
            } catch {
                commands = {};
            }

            this._view.webview.postMessage({
                type: 'queryResult',
                query,
                content: responseContent,
                envReport,
                commands
            });
        } catch (err: any) {
            console.error('handleQuery error:', err);
            this._view.webview.postMessage({
                type: 'queryResult',
                query,
                content: `❌ **WIA Error:** ${err.message || String(err)}`
            });
        }
    }

    private handleOpenFile(filePath: string, line?: number) {
        const root = this.getRootPath();
        if (!root) return;
        const fullPath = path.isAbsolute(filePath) ? filePath : path.join(root, filePath);
        const uri = vscode.Uri.file(fullPath);
        const options: vscode.TextDocumentShowOptions = {};
        if (line && line > 0) {
            const pos = new vscode.Position(line - 1, 0);
            options.selection = new vscode.Range(pos, pos);
        }
        vscode.window.showTextDocument(uri, options);
    }

    // ==========================================
    // CLEAN, STATE-DRIVEN HTML GENERATION
    // ==========================================

    private getHtmlForNoWorkspace(): string {
        return this.wrapHtml(`
            <div class="center-card">
                <h2>Workspace Required</h2>
                <p>Open a project folder to enable Workspace Intelligence Agent.</p>
            </div>
        `);
    }

    private getHtmlForOnboarding(): string {
        return this.wrapHtml(`
            <div class="onboarding-card">
                <div class="brand-header">
                    <span class="brand-icon">⚡</span>
                    <h2>Welcome to WIA</h2>
                </div>
                <div class="subtitle">Workspace Intelligence Agent</div>
                <p class="desc">Configure your AI provider to enable semantic reasoning grounded in your repository.</p>

                <div class="form-group">
                    <label>AI Provider</label>
                    <select id="providerSelect" class="form-control" onchange="onProviderChange()">
                        <option value="openrouter" selected>OpenRouter (Recommended)</option>
                        <option value="nvidia">NVIDIA NIM</option>
                        <option value="openai">OpenAI (GPT-4o)</option>
                        <option value="anthropic">Anthropic (Claude 3.5)</option>
                        <option value="gemini">Google Gemini</option>
                        <option value="local">Offline Local Engine (No API Key)</option>
                    </select>
                </div>

                <div class="form-group" id="modelGroup">
                    <label>Model</label>
                    <input type="text" id="modelInput" class="form-control" value="anthropic/claude-3.5-sonnet" />
                </div>

                <div class="form-group" id="apiKeyGroup">
                    <label>API Key</label>
                    <input type="password" id="apiKeyInput" class="form-control" placeholder="sk-or-v1-..." />
                    <small class="helper-text">Key is stored securely in VS Code SecretStorage.</small>
                </div>

                <div id="testStatusMessage" class="status-msg"></div>

                <div class="button-row">
                    <button class="btn btn-secondary" id="btnVerify" type="button" onclick="testConnection()">Verify Connection</button>
                    <button class="btn btn-primary" id="btnSave" type="button" onclick="saveConfiguration()">Save & Continue</button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                const defaultModels = {
                    openrouter: 'anthropic/claude-3.5-sonnet',
                    nvidia: 'meta/llama-3.1-70b-instruct',
                    openai: 'gpt-4o',
                    anthropic: 'claude-3-5-sonnet-20241022',
                    gemini: 'gemini-1.5-flash',
                    local: 'offline-deterministic'
                };

                function onProviderChange() {
                    const sel = document.getElementById('providerSelect').value;
                    const modelInput = document.getElementById('modelInput');
                    const apiKeyGroup = document.getElementById('apiKeyGroup');
                    modelInput.value = defaultModels[sel] || '';

                    if (sel === 'local') {
                        apiKeyGroup.style.display = 'none';
                    } else {
                        apiKeyGroup.style.display = 'block';
                    }
                }
                window.onProviderChange = onProviderChange;

                function testConnection() {
                    const provider = document.getElementById('providerSelect').value;
                    const apiKey = document.getElementById('apiKeyInput').value;
                    if (vscode && vscode.postMessage) {
                        vscode.postMessage({ type: 'testConnection', provider, apiKey });
                    }
                }
                window.testConnection = testConnection;

                function saveConfiguration() {
                    const provider = document.getElementById('providerSelect').value;
                    const model = document.getElementById('modelInput').value;
                    const apiKey = document.getElementById('apiKeyInput').value;
                    if (vscode && vscode.postMessage) {
                        vscode.postMessage({ type: 'saveAiConfig', provider, model, apiKey });
                    }
                }
                window.saveConfiguration = saveConfiguration;

                const btnVerify = document.getElementById('btnVerify');
                if (btnVerify) btnVerify.addEventListener('click', testConnection);
                const btnSave = document.getElementById('btnSave');
                if (btnSave) btnSave.addEventListener('click', saveConfiguration);

                window.addEventListener('message', event => {
                    const msg = event.data;
                    if (msg && msg.type === 'testStatus') {
                        const el = document.getElementById('testStatusMessage');
                        if (el) {
                            el.innerText = msg.message;
                            el.className = 'status-msg ' + msg.status;
                        }
                    }
                });
            </script>
        `);
    }

    private getHtmlForAuthorization(): string {
        const root = this.getRootPath();
        const wsName = root ? path.basename(root) : 'Workspace';
        return this.wrapHtml(`
            <div class="onboarding-card">
                <div class="brand-header">
                    <span class="brand-icon">🛡️</span>
                    <h2>Workspace Authorization</h2>
                </div>
                <div class="subtitle">${escapeHtml(wsName)}</div>
                <p class="desc">
                    WIA will analyze the local AST structure, package manifests, and architecture of this workspace.
                </p>

                <div class="perm-card">
                    <div class="perm-item">✓ Deterministic local AST symbol indexing</div>
                    <div class="perm-item">✓ Architecture boundaries & dependency cycle audit</div>
                    <div class="perm-item">✓ Environment health & package conflict detection</div>
                </div>

                <div class="button-row" style="margin-top: 20px;">
                    <button class="btn btn-primary" id="btnAuth" type="button" onclick="authorize()">Authorize & Analyze Workspace</button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                function authorize() {
                    if (vscode && vscode.postMessage) {
                        vscode.postMessage({ type: 'authorizeWorkspace' });
                    }
                }
                window.authorize = authorize;
                const btnAuth = document.getElementById('btnAuth');
                if (btnAuth) btnAuth.addEventListener('click', authorize);
            </script>
        `);
    }

    private getHtmlForAnalysisProgress(): string {
        return this.wrapHtml(`
            <div class="center-card">
                <div class="spinner"></div>
                <h2>Initializing Workspace Intelligence</h2>
                <div id="progressStep" class="progress-step">Executing WIA initial indexing...</div>
                <div class="progress-bar-container">
                    <div id="progressBar" class="progress-bar" style="width: 25%;"></div>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                window.addEventListener('message', event => {
                    const msg = event.data;
                    if (msg && msg.type === 'analysisProgress') {
                        const s = document.getElementById('progressStep');
                        const b = document.getElementById('progressBar');
                        if (s) s.innerText = msg.step;
                        if (b) b.style.width = msg.percent + '%';
                    }
                });
            </script>
        `);
    }

    private getHtmlForDashboard(): string {
        const wi = this.workspaceIntelligence;
        const health = wi?.health || { status: 'healthy', errors: [], warnings: [], info: [] };
        const errors = health.errors || [];
        const warnings = health.warnings || [];
        const allIssues = [...errors, ...warnings];
        const totalIssues = allIssues.length;
        const isHealthy = totalIssues === 0;

        const root = this.getRootPath();
        const wsName = wi?.project.name && wi.project.name !== 'Unknown' ? wi.project.name : (root ? path.basename(root) : 'Workspace');
        
        let techStack = 'Workspace Intelligence';
        if (wi?.techStack.frameworks && wi.techStack.frameworks.length > 0 && wi.techStack.frameworks[0] !== 'None') {
            techStack = wi.techStack.frameworks.join(', ');
        } else if (wi?.project.primaryLanguage && wi.project.primaryLanguage !== 'None' && wi.project.primaryLanguage !== 'Unknown') {
            techStack = wi.project.primaryLanguage;
        }

        const totalFiles = wi?.repository.totalFiles || 0;
        const totalSymbols = wi?.codebase.symbols || 0;
        const classes = wi?.codebase.classes || 0;
        const functions = wi?.codebase.functions || 0;
        const subsystems = wi?.architecture.subsystems || [];

        let issuesHtml = '';
        if (totalIssues > 0) {
            issuesHtml = `
                <div class="card-section issues-section">
                    <div class="card-sec-title">⚠️ Workspace Issues (${totalIssues})</div>
                    <div class="issues-list">
                        ${allIssues.map(issue => `
                            <div class="issue-item ${issue.severity}">
                                <div class="issue-title"><strong>${escapeHtml(issue.title)}</strong> <span class="issue-source">(${escapeHtml(issue.source)})</span></div>
                                <div class="issue-msg">${escapeHtml(issue.message)}</div>
                                <div class="issue-evidence"><em>Evidence:</em> ${escapeHtml(issue.evidence)}</div>
                                ${issue.fix ? `<div class="issue-fix"><em>Fix:</em> ${escapeHtml(issue.fix)}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Build initial overview card HTML
        let initialHtml = `
            <div class="overview-header-card">
                <div class="card-title-row">
                    <span class="card-title">⚡ Workspace Intelligence Summary</span>
                    <span class="status-pill ${isHealthy ? 'pill-healthy' : 'pill-warn'}">
                        ${isHealthy ? '✓ Workspace Healthy' : '⚠ ' + totalIssues + (totalIssues === 1 ? ' Issue' : ' Issues')}
                    </span>
                </div>
                <div class="card-stats-grid">
                    <div class="stat-box">
                        <div class="stat-num">${totalFiles}</div>
                        <div class="stat-lbl">Indexed Files</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-num">${totalSymbols}</div>
                        <div class="stat-lbl">AST Symbols</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-num">${classes}</div>
                        <div class="stat-lbl">Classes</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-num">${functions}</div>
                        <div class="stat-lbl">Functions</div>
                    </div>
                </div>

                ${issuesHtml}

                <div class="card-section">
                    <div class="card-sec-title">Architectural Subsystems</div>
                    <div class="subsystems-list">
                        ${subsystems.map((s: any) => `
                            <div class="subsystem-item">
                                <span class="sub-name">${escapeHtml(s.name)}</span>
                                <span class="sub-role">${escapeHtml(s.role)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="quick-action-row">
                    <button class="action-chip" onclick="askQuick('Show architecture')">🗺️ Architecture</button>
                    <button class="action-chip" onclick="askQuick('Check dependencies')">📦 Dependencies</button>
                    <button class="action-chip" onclick="askQuick('Check environment')">🩺 Doctor</button>
                    <button class="action-chip" onclick="askQuick('Show project status')">📊 Status</button>
                </div>
            </div>
        `;

        return this.wrapHtml(`
            <div class="dashboard-header">
                <div class="brand-row">
                    <div class="title-group">
                        <span class="brand-title">WIA</span>
                        <span class="status-pill ${isHealthy ? 'pill-healthy' : errors.length > 0 ? 'pill-error' : 'pill-warn'}">
                            ${isHealthy ? '● Ready' : errors.length > 0 ? '✕ ' + errors.length + (errors.length === 1 ? ' Error' : ' Errors') : '⚠ ' + warnings.length + (warnings.length === 1 ? ' Issue' : ' Issues')}
                        </span>
                    </div>
                    <button class="icon-btn" onclick="openSettings()" title="Settings">⚙</button>
                </div>
                <div class="project-meta">
                    <div class="proj-name">${escapeHtml(wsName)}</div>
                    <div class="proj-stack">${escapeHtml(techStack)}</div>
                </div>

                <div class="quick-nav-pills">
                    <button class="nav-pill" onclick="triggerTab('architecture')">Architecture</button>
                    <button class="nav-pill" onclick="triggerTab('dependencies')">Dependencies</button>
                    <button class="nav-pill" onclick="triggerTab('environment')">Environment</button>
                    <button class="nav-pill" onclick="triggerTab('status')">Status</button>
                </div>
            </div>

            <div class="chat-container" id="chatContainer">
                <div class="message assistant-message">
                    <div class="msg-content">
                        ${initialHtml}
                    </div>
                </div>
            </div>

            <div class="chat-input-bar">
                <textarea id="chatInput" placeholder="Ask anything about this workspace..." rows="2"></textarea>
                <button class="btn-send" id="btnSend" type="button" onclick="sendQuery()">Send</button>
            </div>

            <script>
                const vscode = acquireVsCodeApi();

                window.openSettings = function() {
                    if (vscode && vscode.postMessage) vscode.postMessage({ type: 'openSettings' });
                };

                window.triggerTab = function(tab) {
                    let label = 'Show architecture';
                    if (tab === 'dependencies') label = 'Check dependencies';
                    else if (tab === 'environment') label = 'Check environment';
                    else if (tab === 'status') label = 'Show project status';
                    window.askQuick(label);
                };

                window.askQuick = function(query) {
                    appendUserMessage(query);
                    showStatus('Routing query via Laya: ' + query + '...');
                    if (vscode && vscode.postMessage) {
                        vscode.postMessage({ type: 'askAgent', query: query });
                    }
                };

                window.authorizeRepair = function(cmd) {
                    if (vscode && vscode.postMessage) vscode.postMessage({ type: 'authorizeRepair', command: cmd });
                };

                function sendQuery() {
                    try {
                        const input = document.getElementById('chatInput');
                        if (!input) return;
                        const query = (input.value || '').trim();
                        if (!query) return;

                        input.value = '';
                        input.style.height = 'auto';
                        appendUserMessage(query);
                        showStatus('Routing query via Laya: ' + query + '...');
                        if (vscode && vscode.postMessage) {
                            vscode.postMessage({ type: 'askAgent', query: query });
                        }
                    } catch (err) {
                        console.error('sendQuery error:', err);
                    }
                }
                window.sendQuery = sendQuery;

                function handleKey(e) {
                    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
                        e.preventDefault();
                        sendQuery();
                    }
                }

                function showStatus(text) {
                    const existing = document.getElementById('tempStatus');
                    if (existing) existing.remove();

                    const c = document.getElementById('chatContainer');
                    if (c) {
                        const div = document.createElement('div');
                        div.id = 'tempStatus';
                        div.className = 'status-indicator';
                        div.innerHTML = '<span class="spin-dot">●</span> ' + escapeText(text);
                        c.appendChild(div);
                        c.scrollTop = c.scrollHeight;
                    }
                }

                function appendUserMessage(text) {
                    const c = document.getElementById('chatContainer');
                    if (!c) return;
                    const div = document.createElement('div');
                    div.className = 'message user-message';
                    div.innerHTML = '<div class="msg-content">' + escapeText(text) + '</div>';
                    c.appendChild(div);
                    c.scrollTop = c.scrollHeight;
                }

                function appendAssistantMessage(html) {
                    const c = document.getElementById('chatContainer');
                    if (!c) return;
                    const div = document.createElement('div');
                    div.className = 'message assistant-message';
                    div.innerHTML = '<div class="msg-content">' + html + '</div>';
                    c.appendChild(div);
                    c.scrollTop = c.scrollHeight;
                }

                function escapeText(str) {
                    if (!str) return '';
                    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\\r?\\n/g, '<br/>');
                }

                function renderImpactCard(raw) {
                    if (!raw) return null;
                    var text = raw.replace(/\x1B\[[0-9;]*[mK]/g, '');
                    if (text.indexOf("Impact Analysis for '") === -1 && text.indexOf("Target Entity:") === -1) {
                        return null;
                    }

                    var targetMatch = text.match(/Impact Analysis for '([^']+)'/) || text.match(/Target Entity:\s*(.*)/);
                    var target = targetMatch ? targetMatch[1].trim() : 'Entity';

                    var definedMatch = text.match(/Defined In:\s*(.*)/);
                    var definedIn = definedMatch ? definedMatch[1].trim() : '';

                    var typeMatch = text.match(/Target Type:\s*(.*)/);
                    var targetType = typeMatch ? typeMatch[1].trim() : 'symbol';

                    var riskMatch = text.match(/Risk Classification:\s*(HIGH|MEDIUM|LOW)/i);
                    var risk = riskMatch ? riskMatch[1].toUpperCase() : 'LOW';
                    var riskClass = risk.toLowerCase();

                    var explMatch = text.match(/Explanation:\s*([\s\S]*?)(?=\\r?\\n\\r?\\n|\\r?\\n[A-Z][a-zA-Z\\s\\-]+(?:\\(\\d+\\))?:|$)/);
                    var explanation = explMatch ? explMatch[1].trim() : '';

                    function extractList(headerRegex) {
                        var match = text.match(headerRegex);
                        if (!match) return [];
                        var lines = match[1].split(/\\r?\\n/);
                        var items = [];
                        for (var i = 0; i < lines.length; i++) {
                            var trimmed = lines[i].trim();
                            if (trimmed.startsWith('*') || trimmed.startsWith('-')) {
                                var item = trimmed.replace(/^[\\*\\-]\\s*/, '').trim();
                                if (item && !item.toLowerCase().startsWith('no ') && item.indexOf('additional consuming modules') === -1 && item.indexOf('additional affected files') === -1) {
                                    items.push(item);
                                }
                            }
                        }
                        return items;
                    }

                    var callers = extractList(/(?:Direct Symbol Callers|File-Level Dependents[^:\n]*):\s*([\s\S]*?)(?=\\r?\\n===|\\r?\\n[A-Z][a-zA-Z\\s\\-]+(?:\\(\\d+\\))?:|$)/);
                    var affected = extractList(/Affected Files[^:\n]*:\s*([\s\S]*?)(?=\\r?\\n===|\\r?\\n[A-Z][a-zA-Z\\s\\-]+(?:\\(\\d+\\))?:|$)/);

                    var callersHtml = '';
                    if (callers.length > 0) {
                        var cItems = '';
                        for (var j = 0; j < callers.length; j++) {
                            var c = callers[j];
                            var cleanPath = c.replace(/\\s*\\(.*?\\)$/, '').trim();
                            cItems += '<div class="impact-file-item" onclick="vscode.postMessage({type:\'openFile\',filePath:\'' + cleanPath.replace(/'/g, "\\'") + '\'})" title="Click to open ' + cleanPath + '">📄 ' + escapeText(c) + '</div>';
                        }
                        callersHtml = '<div class="impact-section">' +
                            '<div class="impact-sec-title">Direct Callers / Dependents (' + callers.length + ')</div>' +
                            '<div class="impact-file-list">' + cItems + '</div>' +
                        '</div>';
                    }

                    var affectedHtml = '';
                    if (affected.length > 0) {
                        var aItems = '';
                        for (var k = 0; k < affected.length; k++) {
                            var a = affected[k];
                            aItems += '<div class="impact-file-item" onclick="vscode.postMessage({type:\'openFile\',filePath:\'' + a.replace(/'/g, "\\'") + '\'})" title="Click to open ' + a + '">📄 ' + escapeText(a) + '</div>';
                        }
                        var isOpen = callers.length === 0 ? ' open' : '';
                        affectedHtml = '<details class="impact-details"' + isOpen + '>' +
                            '<summary>Affected Files (' + affected.length + ')</summary>' +
                            '<div class="impact-file-list" style="margin-top: 6px;">' + aItems + '</div>' +
                        '</details>';
                    }

                    var definedHtml = definedIn ? '<span class="impact-tag file-tag" onclick="vscode.postMessage({type:\'openFile\',filePath:\'' + definedIn.replace(/'/g, "\\'") + '\'})" title="Open ' + definedIn + '">📁 ' + escapeText(definedIn) + '</span>' : '';
                    var explHtml = explanation ? '<div class="impact-explanation">' + escapeText(explanation) + '</div>' : '';

                    return '<div class="impact-card">' +
                        '<div class="impact-header-row">' +
                            '<div class="impact-title-group">' +
                                '<span class="impact-icon">⚡</span>' +
                                '<span class="impact-title">Impact: <strong>' + escapeText(target) + '</strong></span>' +
                            '</div>' +
                            '<span class="risk-badge risk-' + riskClass + '">' + risk + ' RISK</span>' +
                        '</div>' +
                        '<div class="impact-meta-row">' +
                            '<span class="impact-tag"><span class="tag-lbl">Type:</span> ' + escapeText(targetType) + '</span>' +
                            definedHtml +
                        '</div>' +
                        explHtml +
                        callersHtml +
                        affectedHtml +
                    '</div>';
                }

                function formatMarkdown(str) {
                    if (!str) return '';
                    let out = String(str);

                    // Strip ANSI color codes from CLI outputs
                    out = out.replace(/\x1B\[[0-9;]*[mK]/g, '');

                    // Check for specialized card renderers
                    const impactCard = renderImpactCard(out);
                    if (impactCard) {
                        return impactCard;
                    }

                    // 1. Extract and preserve code blocks
                    const codeBlocks = [];
                    out = out.replace(new RegExp('\\x60\\x60\\x60([a-zA-Z0-9_-]*)\\r?\\n([\\s\\S]*?)\\x60\\x60\\x60', 'gi'), (match, lang, code) => {
                        const id = '___CODEBLOCK_' + codeBlocks.length + '___';
                        const escaped = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        codeBlocks.push('<pre class="code-block"><code>' + escaped + '</code></pre>');
                        return id;
                    });

                    // 2. Escape HTML
                    out = out.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

                    // 3. Section dividers (e.g. === Architecture Intelligence ===)
                    out = out.replace(/^=== (.*?) ===$/gim, '<div class="section-divider">$1</div>');

                    // 4. Headers
                    out = out.replace(/^#### (.*$)/gim, '<h4 class="md-h4">$1</h4>');
                    out = out.replace(/^### (.*$)/gim, '<h3 class="md-h3">$1</h3>');
                    out = out.replace(/^## (.*$)/gim, '<h2 class="md-h2">$1</h2>');
                    out = out.replace(/^# (.*$)/gim, '<h1 class="md-h1">$1</h1>');

                    // 5. Bold and Italic
                    out = out.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                    out = out.replace(/\\*(.*?)\\*/g, '<em>$1</em>');

                    // 6. Inline code
                    out = out.replace(new RegExp('\\x60([^\\x60]+)\\x60', 'g'), '<code>$1</code>');

                    // 7. Bullet lists
                    out = out.replace(/^\\s*[\\*\\-]\\s+(.*$)/gim, '<div class="list-item"><span class="bullet">•</span> $1</div>');

                    // 8. Newlines
                    out = out.replace(/\\r?\\n/g, '<br/>');

                    // 9. Restore code blocks
                    codeBlocks.forEach((block, idx) => {
                        out = out.replace('___CODEBLOCK_' + idx + '___', block);
                    });

                    return out;
                }

                // Attach event listeners & delegation
                const chatInputEl = document.getElementById('chatInput');
                if (chatInputEl) {
                    chatInputEl.addEventListener('keydown', handleKey);
                }
                const btnSendEl = document.getElementById('btnSend');
                if (btnSendEl) {
                    btnSendEl.addEventListener('click', function(e) {
                        e.preventDefault();
                        sendQuery();
                    });
                }

                // Global event delegation for all buttons and chips
                document.addEventListener('click', function(e) {
                    const target = e.target;
                    if (!target) return;

                    // Send Button
                    if (target.id === 'btnSend' || target.closest('#btnSend')) {
                        e.preventDefault();
                        sendQuery();
                        return;
                    }

                    // Settings Button
                    if (target.classList.contains('icon-btn') || target.closest('.icon-btn')) {
                        e.preventDefault();
                        window.openSettings();
                        return;
                    }

                    // Nav Pills
                    const navPill = target.closest('.nav-pill');
                    if (navPill) {
                        e.preventDefault();
                        const txt = navPill.textContent.trim().toLowerCase();
                        window.triggerTab(txt);
                        return;
                    }

                    // Quick Action Chips
                    const actionChip = target.closest('.action-chip');
                    if (actionChip) {
                        e.preventDefault();
                        const query = actionChip.textContent.replace(/^[^\w]+/, '').trim();
                        window.askQuick(query);
                        return;
                    }
                });

                window.addEventListener('message', event => {
                    const msg = event.data;
                    if (!msg) return;
                    if (msg.type === 'queryStarted') {
                        // status indicated
                    } else if (msg.type === 'statusUpdate') {
                        showStatus(msg.step);
                    } else if (msg.type === 'queryResult') {
                        const temp = document.getElementById('tempStatus');
                        if (temp) temp.remove();

                        appendAssistantMessage(formatMarkdown(msg.content));
                    }
                });
            </script>
        `);
    }

    private wrapHtml(bodyContent: string): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; script-src * 'unsafe-inline' 'unsafe-eval' vscode-resource:; style-src * 'unsafe-inline'; font-src * data:; img-src * data: blob: vscode-resource:;">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIA</title>
    <style>
        * {
            box-sizing: border-box;
        }
        :root {
            --bg: var(--vscode-sideBar-background, #1e1e1e);
            --fg: var(--vscode-foreground, #cccccc);
            --card-bg: var(--vscode-editor-background, #252526);
            --border: var(--vscode-panel-border, rgba(255, 255, 255, 0.1));
            --accent: var(--vscode-button-background, #0e639c);
            --accent-hover: var(--vscode-button-hoverBackground, #1177bb);
            --badge-green: #3fb950;
            --badge-yellow: #d29922;
            --input-bg: var(--vscode-input-background, #3c3c3c);
        }
        body {
            font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            background-color: var(--bg);
            color: var(--fg);
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
            font-size: 13px;
        }
        .dashboard-header {
            padding: 12px;
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .brand-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .title-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .brand-title {
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.5px;
        }
        .status-pill {
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 10px;
            font-weight: 500;
        }
        .pill-healthy {
            background: rgba(63, 185, 80, 0.15);
            color: var(--badge-green);
        }
        .pill-warn {
            background: rgba(210, 153, 34, 0.15);
            color: var(--badge-yellow);
        }
        .icon-btn {
            background: transparent;
            border: none;
            color: var(--fg);
            cursor: pointer;
            font-size: 14px;
            opacity: 0.7;
            padding: 4px;
        }
        .icon-btn:hover { opacity: 1; }
        .project-meta {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .proj-name {
            font-weight: 600;
            font-size: 13px;
        }
        .proj-stack {
            font-size: 11px;
            color: var(--vscode-descriptionForeground, #8b949e);
        }
        .quick-nav-pills {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 4px;
        }
        .nav-pill {
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--fg);
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .nav-pill:hover {
            border-color: var(--accent);
            color: var(--accent);
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            width: 100%;
        }
        .message {
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 100%;
        }
        .user-message {
            align-self: flex-end;
            max-width: 85%;
        }
        .user-message .msg-content {
            background: var(--accent);
            color: #ffffff;
            border-radius: 10px 10px 2px 10px;
            padding: 8px 12px;
            word-break: break-word;
            overflow-wrap: break-word;
        }
        .assistant-message {
            align-self: flex-start;
            width: 100%;
        }
        .assistant-message .msg-content {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 10px 10px 10px 2px;
            padding: 10px 12px;
            line-height: 1.5;
            font-size: 12.5px;
            min-width: 0;
            max-width: 100%;
            overflow-wrap: break-word;
            word-break: break-word;
        }
        .md-h1, .md-h2, .md-h3, .md-h4 {
            margin: 10px 0 4px 0;
            font-weight: 600;
            color: var(--fg);
        }
        .md-h1 { font-size: 15px; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
        .md-h2 { font-size: 14px; border-bottom: 1px solid var(--border); padding-bottom: 2px; }
        .md-h3 { font-size: 13px; color: var(--accent-hover); }
        .md-h4 { font-size: 12px; }
        .section-divider {
            font-weight: 700;
            color: var(--accent);
            background: rgba(14, 99, 156, 0.1);
            border-left: 3px solid var(--accent);
            padding: 4px 8px;
            margin: 10px 0 6px 0;
            border-radius: 0 4px 4px 0;
            font-size: 12px;
        }
        .list-item {
            margin: 2px 0;
            padding-left: 4px;
            display: flex;
            align-items: flex-start;
            gap: 6px;
        }
        .bullet {
            color: var(--accent);
            font-weight: bold;
        }
        .overview-header-card {
            display: flex;
            flex-direction: column;
            gap: 12px;
            width: 100%;
        }
        .card-title-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .card-title {
            font-weight: 700;
            font-size: 13px;
            color: var(--fg);
        }
        .card-stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(65px, 1fr));
            gap: 6px;
            width: 100%;
        }
        .stat-box {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 6px 4px;
            text-align: center;
            min-width: 0;
        }
        .stat-num {
            font-size: 14px;
            font-weight: 700;
            color: var(--accent);
        }
        .stat-lbl {
            font-size: 10px;
            color: var(--vscode-descriptionForeground, #8b949e);
            margin-top: 2px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .impact-card {
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px;
            width: 100%;
        }
        .impact-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .impact-title-group {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
        }
        .impact-meta-row {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            align-items: center;
        }
        .impact-tag {
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 3px;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--fg);
        }
        .impact-tag.file-tag {
            cursor: pointer;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .impact-tag.file-tag:hover {
            border-color: var(--accent);
            color: var(--accent);
        }
        .tag-lbl {
            color: var(--vscode-descriptionForeground, #8b949e);
            margin-right: 2px;
        }
        .risk-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .risk-high {
            background: rgba(248, 81, 73, 0.15);
            color: #f85149;
            border: 1px solid rgba(248, 81, 73, 0.4);
        }
        .risk-medium {
            background: rgba(210, 153, 34, 0.15);
            color: #d29922;
            border: 1px solid rgba(210, 153, 34, 0.4);
        }
        .risk-low {
            background: rgba(63, 185, 80, 0.15);
            color: #3fb950;
            border: 1px solid rgba(63, 185, 80, 0.4);
        }
        .impact-explanation {
            font-size: 12px;
            color: var(--fg);
            line-height: 1.4;
            background: rgba(255, 255, 255, 0.03);
            padding: 6px 8px;
            border-radius: 4px;
            border-left: 2px solid var(--accent);
        }
        .impact-section {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: 4px;
        }
        .impact-sec-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--vscode-descriptionForeground, #8b949e);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .impact-file-list {
            display: flex;
            flex-direction: column;
            gap: 3px;
            max-height: 180px;
            overflow-y: auto;
            background: var(--bg);
            padding: 6px;
            border-radius: 4px;
            border: 1px solid var(--border);
        }
        .impact-file-item {
            font-family: var(--vscode-editor-font-family, monospace);
            font-size: 11px;
            color: var(--fg);
            cursor: pointer;
            padding: 3px 5px;
            border-radius: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .impact-file-item:hover {
            background: rgba(14, 99, 156, 0.15);
            color: var(--accent);
        }
        .impact-details {
            margin-top: 4px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 4px 6px;
        }
        .impact-details summary {
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            color: var(--vscode-descriptionForeground, #8b949e);
            outline: none;
        }
        .impact-details[open] summary {
            margin-bottom: 6px;
        }
        .card-section {
            display: flex;
            flex-direction: column;
            gap: 6px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 8px 10px;
        }
        .card-sec-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--vscode-descriptionForeground, #8b949e);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .subsystems-list {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .subsystem-item {
            display: flex;
            flex-direction: column;
            font-size: 11.5px;
            padding-bottom: 4px;
            border-bottom: 1px solid var(--border);
        }
        .subsystem-item:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }
        .sub-name {
            font-weight: 600;
            color: var(--fg);
        }
        .sub-role {
            font-size: 10.5px;
            color: var(--vscode-descriptionForeground, #8b949e);
        }
        .quick-action-row {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 4px;
        }
        .action-chip {
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--fg);
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .action-chip:hover {
            border-color: var(--accent);
            color: var(--accent);
            background: rgba(14, 99, 156, 0.1);
        }
        .code-block {
            background: var(--bg);
            padding: 8px 10px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: var(--vscode-editor-font-family, monospace);
            font-size: 11.5px;
            border: 1px solid var(--border);
            margin: 8px 0;
            white-space: pre;
            line-height: 1.4;
        }
        .chat-input-bar {
            padding: 8px 12px;
            background: var(--card-bg);
            border-top: 1px solid var(--border);
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }
        textarea {
            flex: 1;
            background: var(--input-bg);
            color: var(--fg);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 6px 8px;
            resize: none;
            font-family: inherit;
            font-size: 12px;
            outline: none;
        }
        textarea:focus {
            border-color: var(--accent);
        }
        .btn-send {
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 7px 14px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        }
        .btn-send:hover {
            background: var(--accent-hover);
        }
        .status-indicator {
            font-size: 11px;
            color: var(--vscode-descriptionForeground, #8b949e);
            padding: 4px 8px;
            font-style: italic;
        }
        .spin-dot {
            color: var(--accent);
            animation: pulse 1s infinite alternate;
        }
        @keyframes pulse { from { opacity: 0.3; } to { opacity: 1; } }

        /* Onboarding styles */
        .onboarding-card, .center-card {
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin: auto;
            max-width: 320px;
        }
        .brand-header {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-icon { font-size: 24px; }
        .subtitle { font-weight: 500; color: var(--vscode-descriptionForeground, #8b949e); }
        .desc { font-size: 12px; line-height: 1.4; }
        .form-group { display: flex; flex-direction: column; gap: 4px; }
        .form-control {
            background: var(--input-bg);
            color: var(--fg);
            border: 1px solid var(--border);
            padding: 6px 8px;
            border-radius: 4px;
        }
        .helper-text { font-size: 11px; opacity: 0.7; }
        .button-row { display: flex; gap: 8px; margin-top: 10px; }
        .btn {
            flex: 1;
            padding: 7px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-weight: 500;
        }
        .btn-primary { background: var(--accent); color: #fff; }
        .btn-secondary { background: var(--card-bg); color: var(--fg); border: 1px solid var(--border); }
        .status-msg { font-size: 11px; padding: 4px 0; }
        .status-msg.success { color: var(--badge-green); }
        .status-msg.error { color: #f85149; }
        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .progress-bar-container {
            height: 4px;
            background: var(--border);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 8px;
        }
        .progress-bar {
            height: 100%;
            background: var(--accent);
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    ${bodyContent}
</body>
</html>`;
    }
}
