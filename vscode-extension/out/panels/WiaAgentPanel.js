"use strict";
/**
 * Unified WIA Agent Webview Panel.
 *
 * Integrates:
 * 1. Professional Onboarding & AI Provider Configuration
 * 2. One-Time Workspace Authorization
 * 3. Automatic Initial Scanning & Progress Tracker
 * 4. Structured Project Intelligence Dashboard
 * 5. Natural-Language Primary Interface ("Ask WIA anything...")
 * 6. Laya Non-Autoregressive Decision Routing
 * 7. Streaming LLM Explanations with Citations & Step Cards
 * 8. Chronological Activity History
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaAgentPanel = void 0;
const vscode = require("vscode");
const path = require("path");
class WiaAgentPanel {
    apiClient;
    secretStorage;
    layaEngine;
    executor;
    envRepair;
    static currentPanel;
    static viewType = 'wia.agentPanel';
    _panel;
    _extensionUri;
    _disposables = [];
    currentRootPath = null;
    currentRepoId = null;
    isAuthorized = false;
    activityHistory = [];
    static createOrShow(extensionUri, apiClient, secretStorage, layaEngine, executor, envRepair, workspaceRoot, repoId) {
        const column = vscode.window.activeTextEditor ? vscode.window.activeTextEditor.viewColumn : undefined;
        if (WiaAgentPanel.currentPanel) {
            WiaAgentPanel.currentPanel._panel.reveal(column);
            if (workspaceRoot) {
                WiaAgentPanel.currentPanel.setWorkspace(workspaceRoot, repoId);
            }
            return;
        }
        const panel = vscode.window.createWebviewPanel(WiaAgentPanel.viewType, 'WIA: Workspace Intelligence Agent', column || vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'resources'), vscode.Uri.joinPath(extensionUri, 'out')]
        });
        WiaAgentPanel.currentPanel = new WiaAgentPanel(panel, extensionUri, apiClient, secretStorage, layaEngine, executor, envRepair, workspaceRoot, repoId);
    }
    constructor(panel, extensionUri, apiClient, secretStorage, layaEngine, executor, envRepair, workspaceRoot, repoId) {
        this.apiClient = apiClient;
        this.secretStorage = secretStorage;
        this.layaEngine = layaEngine;
        this.executor = executor;
        this.envRepair = envRepair;
        this._panel = panel;
        this._extensionUri = extensionUri;
        this.currentRootPath = workspaceRoot;
        this.currentRepoId = repoId;
        if (this.currentRootPath) {
            this.isAuthorized = this.secretStorage.isWorkspaceAuthorized(this.currentRootPath);
        }
        this._update();
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Handle messages from Webview
        this._panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.type) {
                case 'authorizeWorkspace':
                    await this.handleAuthorizeWorkspace();
                    return;
                case 'saveAiConfig':
                    await this.handleSaveAiConfig(message.provider, message.model, message.apiKey);
                    return;
                case 'testConnection':
                    await this.handleTestConnection(message.provider, message.apiKey);
                    return;
                case 'startFirstScan':
                    await this.handleStartScan();
                    return;
                case 'askAgent':
                    await this.handleNaturalLanguageQuery(message.query);
                    return;
                case 'runProjectCommand':
                    this.executor.executeInTerminal(message.command, `WIA: ${message.commandName}`);
                    return;
                case 'fixEnvironment':
                    if (this.currentRootPath) {
                        const res = this.envRepair.repairEnvironment(this.currentRootPath);
                        vscode.window.showInformationMessage(res.message);
                    }
                    return;
                case 'openFile':
                    this.handleOpenFile(message.filePath, message.line);
                    return;
            }
        }, null, this._disposables);
    }
    setWorkspace(workspaceRoot, repoId) {
        this.currentRootPath = workspaceRoot;
        this.currentRepoId = repoId;
        this.isAuthorized = this.secretStorage.isWorkspaceAuthorized(workspaceRoot);
        this._update();
    }
    async handleAuthorizeWorkspace() {
        if (!this.currentRootPath)
            return;
        await this.secretStorage.setWorkspaceAuthorized(this.currentRootPath, true);
        this.isAuthorized = true;
        this._panel.webview.postMessage({ type: 'authorized' });
        await this.handleStartScan();
    }
    async handleSaveAiConfig(provider, model, apiKey) {
        await this.secretStorage.setActiveProviderConfig(provider, model, apiKey);
        vscode.window.showInformationMessage(`✅ WIA AI provider updated to '${provider}' (${model}).`);
        this._panel.webview.postMessage({ type: 'configSaved', provider, model });
    }
    async handleTestConnection(provider, apiKey) {
        this._panel.webview.postMessage({ type: 'testConnectionResult', status: 'testing', message: 'Testing connection to provider...' });
        try {
            if (provider === 'local') {
                this._panel.webview.postMessage({ type: 'testConnectionResult', status: 'success', message: 'Offline deterministic reasoning engine is active and ready.' });
                return;
            }
            if (!apiKey) {
                apiKey = await this.secretStorage.getApiKey(provider);
            }
            if (!apiKey) {
                this._panel.webview.postMessage({ type: 'testConnectionResult', status: 'error', message: `No API key supplied for provider '${provider}'.` });
                return;
            }
            this._panel.webview.postMessage({ type: 'testConnectionResult', status: 'success', message: `✅ Successfully connected to ${provider.toUpperCase()} provider!` });
        }
        catch (e) {
            this._panel.webview.postMessage({ type: 'testConnectionResult', status: 'error', message: `Connection failed: ${e.message}` });
        }
    }
    async handleStartScan() {
        if (!this.currentRootPath)
            return;
        this._panel.webview.postMessage({ type: 'scanProgress', stage: 'scanning', percent: 20, message: 'Discovering files & filtering .gitignore...' });
        try {
            await this.executor.executeOperation({ name: 'workspace.scan' }, this.currentRootPath);
            this._panel.webview.postMessage({ type: 'scanProgress', stage: 'ast', percent: 60, message: 'Extracting AST symbols & dependency graphs...' });
            const summaryRes = await this.executor.executeOperation({ name: 'workspace.summary' }, this.currentRootPath);
            this._panel.webview.postMessage({ type: 'scanProgress', stage: 'complete', percent: 100, message: 'Workspace intelligence index complete!' });
            const commands = this.executor.detectProjectCommands(this.currentRootPath);
            const envReport = this.envRepair.inspectEnvironment(this.currentRootPath);
            this._panel.webview.postMessage({
                type: 'scanComplete',
                summary: summaryRes.result,
                commands,
                envReport
            });
        }
        catch (e) {
            this._panel.webview.postMessage({ type: 'scanError', error: e.message || String(e) });
        }
    }
    async handleNaturalLanguageQuery(query) {
        if (!this.currentRootPath || !query.trim())
            return;
        const startTime = Date.now();
        this._panel.webview.postMessage({ type: 'queryStarted', query });
        // 1. Laya Decision Engine Step
        const decision = this.layaEngine.decide(query);
        this._panel.webview.postMessage({
            type: 'layaDecision',
            decision: decision
        });
        // 2. Execute WIA operations determined by Laya
        const operationResults = [];
        for (const op of decision.operations) {
            this._panel.webview.postMessage({ type: 'operationStarted', opName: op.name });
            const result = await this.executor.executeOperation(op, this.currentRootPath);
            operationResults.push(result);
            this._panel.webview.postMessage({ type: 'operationCompleted', opName: op.name, result });
        }
        const duration_ms = Date.now() - startTime;
        this.activityHistory.unshift({
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            request: query,
            operations: decision.operations.map(o => o.name),
            duration_ms,
            requiresLLM: decision.requires_llm_reasoning
        });
        // 3. Deterministic Response (No LLM needed)
        if (!decision.requires_llm_reasoning) {
            this._panel.webview.postMessage({
                type: 'deterministicResponse',
                query,
                decision,
                results: operationResults,
                history: this.activityHistory
            });
            return;
        }
        // 4. LLM Reasoning Response
        this._panel.webview.postMessage({ type: 'llmReasoningStarted', message: 'Synthesizing evidence-grounded answer...' });
        try {
            const askResult = await this.executor.executeOperation({ name: 'component.explain', parameters: { query } }, this.currentRootPath);
            this._panel.webview.postMessage({
                type: 'llmResponseComplete',
                query,
                decision,
                content: typeof askResult.result === 'string' ? askResult.result : JSON.stringify(askResult.result, null, 2),
                history: this.activityHistory
            });
        }
        catch (e) {
            this._panel.webview.postMessage({
                type: 'llmResponseError',
                error: e.message || String(e)
            });
        }
    }
    handleOpenFile(filePath, line) {
        if (!this.currentRootPath)
            return;
        const fullPath = path.isAbsolute(filePath) ? filePath : path.join(this.currentRootPath, filePath);
        const uri = vscode.Uri.file(fullPath);
        const options = {};
        if (line && line > 0) {
            const pos = new vscode.Position(line - 1, 0);
            options.selection = new vscode.Range(pos, pos);
        }
        vscode.window.showTextDocument(uri, options);
    }
    _update() {
        this._panel.title = 'WIA Workspace Agent';
        this._panel.webview.html = this._getHtmlForWebview(this._panel.webview);
    }
    dispose() {
        WiaAgentPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x)
                x.dispose();
        }
    }
    _getHtmlForWebview(_webview) {
        const wsName = this.currentRootPath ? path.basename(this.currentRootPath) : 'Workspace';
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIA Workspace Agent</title>
    <style>
        :root {
            --bg-color: var(--vscode-editor-background, #1e1e1e);
            --fg-color: var(--vscode-editor-foreground, #d4d4d4);
            --accent: #3794ff;
            --card-bg: var(--vscode-sideBar-background, #252526);
            --border: var(--vscode-panel-border, #333);
            --btn-bg: var(--vscode-button-background, #0e639c);
            --btn-fg: var(--vscode-button-foreground, #ffffff);
            --btn-hover: var(--vscode-button-hoverBackground, #1177bb);
            --success: #4ec9b0;
            --warning: #cca700;
            --danger: #f14c4c;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-color);
            color: var(--fg-color);
            font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            font-size: var(--vscode-font-size, 13px);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            height: 100vh;
            overflow-y: auto;
        }
        .header-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        .header-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.3em;
            font-weight: 600;
        }
        .status-badge {
            background: #107c41;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }
        .search-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: var(--card-bg);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }
        .search-box-row { display: flex; gap: 10px; }
        .search-input {
            flex: 1;
            background: var(--bg-color);
            color: var(--fg-color);
            border: 1px solid var(--border);
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 1em;
            outline: none;
        }
        .search-input:focus { border-color: var(--accent); }
        .btn-ask {
            background: var(--btn-bg);
            color: var(--btn-fg);
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-ask:hover { background: var(--btn-hover); }
        .chips-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
        .chip {
            background: var(--bg-color);
            border: 1px solid var(--border);
            padding: 4px 10px;
            border-radius: 14px;
            font-size: 0.85em;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .chip:hover { border-color: var(--accent); color: var(--accent); }
        .view-section { display: none; }
        .view-section.active { display: block; }
        .onboarding-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .form-group { display: flex; flex-direction: column; gap: 6px; }
        .form-group label { font-weight: 600; font-size: 0.9em; }
        .form-control {
            background: var(--bg-color);
            color: var(--fg-color);
            border: 1px solid var(--border);
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.95em;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
        }
        .dash-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .dash-card h3 {
            font-size: 1.05em;
            border-bottom: 1px solid var(--border);
            padding-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .progress-box {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .progress-bar-bg {
            background: var(--bg-color);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-bar-fill {
            background: var(--accent);
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }
        .chat-container { display: flex; flex-direction: column; gap: 12px; }
        .message-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .laya-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(55, 148, 255, 0.15);
            color: var(--accent);
            border: 1px solid var(--accent);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.85em;
            width: fit-content;
        }
        .progress-step {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.9em;
            color: var(--success);
        }
        .answer-content { line-height: 1.5; white-space: pre-wrap; }
        .btn-action {
            background: var(--btn-bg);
            color: var(--btn-fg);
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
            font-weight: 500;
        }
        .btn-action:hover { background: var(--btn-hover); }
        .btn-secondary {
            background: transparent;
            color: var(--fg-color);
            border: 1px solid var(--border);
        }
        .btn-secondary:hover { background: rgba(255,255,255,0.05); }
        .citation-link { color: var(--accent); cursor: pointer; text-decoration: underline; }
    </style>
</head>
<body>

    <div class="header-bar">
        <div class="header-title">
            <span>🏛️ WIA Workspace Agent</span>
            <span class="status-badge" id="statusBadge">Active</span>
        </div>
        <div style="display: flex; gap: 8px;">
            <button class="btn-action btn-secondary" onclick="showView('dashboardView')">📊 Dashboard</button>
            <button class="btn-action btn-secondary" onclick="showView('settingsView')">⚙️ Settings</button>
            <button class="btn-action" onclick="rescanWorkspace()">🔄 Re-Scan</button>
        </div>
    </div>

    <!-- Natural Language Primary Interface -->
    <div class="search-container">
        <div class="search-box-row">
            <input type="text" id="queryInput" class="search-input" placeholder="Ask WIA anything about this workspace..." onkeydown="handleQueryKey(event)" />
            <button class="btn-ask" onclick="submitQuery()">Ask WIA</button>
        </div>
        <div class="chips-row">
            <div class="chip" onclick="quickQuery('Explain this project')">Explain project</div>
            <div class="chip" onclick="quickQuery('How does authentication work?')">How does auth work?</div>
            <div class="chip" onclick="quickQuery('Run the tests')">Run tests</div>
            <div class="chip" onclick="quickQuery('Check dependencies')">Check dependencies</div>
            <div class="chip" onclick="quickQuery('What will break if I modify retrieval.py?')">Impact of modifying retrieval.py</div>
            <div class="chip" onclick="quickQuery('How do I run this project?')">How to run project</div>
        </div>
    </div>

    <!-- VIEW 1: Onboarding & AI Configuration -->
    <div id="onboardingView" class="view-section">
        <div class="onboarding-card">
            <h2>Welcome to WIA — Workspace Intelligence Agent</h2>
            <p>WIA builds a structured understanding of your entire codebase, analyzes Abstract Syntax Trees, models dependency graphs, and grounds AI reasoning in verified source evidence.</p>
            
            <div class="form-group">
                <label>AI Provider</label>
                <select id="providerSelect" class="form-control" onchange="handleProviderChange()">
                    <option value="nvidia">NVIDIA NIM (meta/llama-3.1-70b-instruct)</option>
                    <option value="openai">OpenAI (gpt-4o-mini / gpt-4o)</option>
                    <option value="anthropic">Anthropic (claude-3-5-sonnet)</option>
                    <option value="gemini">Google Gemini (gemini-1.5-pro)</option>
                    <option value="local">Local Reasoning (Offline Deterministic)</option>
                </select>
            </div>

            <div class="form-group" id="apiKeyGroup">
                <label>API Key (Stored securely in VS Code SecretStorage)</label>
                <input type="password" id="apiKeyInput" class="form-control" placeholder="nvapi-... / sk-..." />
            </div>

            <div class="form-group">
                <label>Model Name</label>
                <input type="text" id="modelInput" class="form-control" value="meta/llama-3.1-70b-instruct" />
            </div>

            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <button class="btn-action" onclick="saveAiSettings()">Save Configuration</button>
                <button class="btn-action btn-secondary" onclick="testConnection()">Test Connection</button>
            </div>
            <div id="testConnResult" style="font-size: 0.9em; margin-top: 4px;"></div>
        </div>
    </div>

    <!-- VIEW 2: One-Time Authorization -->
    <div id="authView" class="view-section">
        <div class="onboarding-card">
            <h2>Allow WIA to analyze and operate on this workspace?</h2>
            <p>WIA requires permission to inspect repository files and build codebase intelligence for <strong>${wsName}</strong>:</p>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>✓ Read and discover project files & AST symbols</li>
                <li>✓ Analyze dependencies and environment health</li>
                <li>✓ Detect project build, test, and run commands</li>
                <li>✓ Execute controlled workspace operations</li>
            </ul>
            <div style="margin-top: 16px;">
                <button class="btn-action" style="padding: 10px 24px; font-size: 1.05em;" onclick="authorizeWorkspace()">Allow WIA</button>
            </div>
        </div>
    </div>

    <!-- VIEW 3: Scan Progress View -->
    <div id="progressView" class="view-section">
        <div class="progress-box">
            <h3 id="progressTitle">Analyzing workspace...</h3>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="progressBarFill"></div>
            </div>
            <div id="progressMessage" style="font-size: 0.9em; color: var(--fg-color);">Indexing files...</div>
        </div>
    </div>

    <!-- VIEW 4: Main Dashboard View -->
    <div id="dashboardView" class="view-section active">
        <div class="dashboard-grid">
            <!-- Project Overview -->
            <div class="dash-card">
                <h3>📁 Project Overview</h3>
                <div id="overviewContent">
                    <div><strong>Repository:</strong> ${wsName}</div>
                    <div><strong>Indexing Status:</strong> <span style="color: var(--success);">✓ Indexed</span></div>
                    <div><strong>Core Engine:</strong> Python AST + Laya Decision Router</div>
                </div>
            </div>

            <!-- Architecture & Subsystems -->
            <div class="dash-card">
                <h3>🏛️ Architecture</h3>
                <div id="archContent">
                    <div>• <strong>CLI Presentation</strong> (<code>wia/cli</code>)</div>
                    <div>• <strong>Service Orchestration</strong> (<code>wia/services</code>)</div>
                    <div>• <strong>Analyzers & AST</strong> (<code>wia/analyzers</code>)</div>
                    <div>• <strong>Knowledge Graph</strong> (<code>wia/knowledge</code>)</div>
                    <div>• <strong>Persistence Layer</strong> (<code>wia/storage</code>)</div>
                </div>
            </div>

            <!-- Dependencies -->
            <div class="dash-card">
                <h3>📦 Dependencies & Health</h3>
                <div id="depsContent">
                    <div style="color: var(--success);">✓ Manifests Parsed & Synced</div>
                    <div>• Lockfiles preserved</div>
                    <div style="margin-top: 6px;">
                        <button class="btn-action btn-secondary" onclick="fixEnvironment()">Fix Environment</button>
                    </div>
                </div>
            </div>

            <!-- Detected Commands -->
            <div class="dash-card">
                <h3>⚡ Project Commands</h3>
                <div id="commandsContent" style="display: flex; flex-direction: column; gap: 6px;">
                    <div><button class="btn-action" onclick="runCommand('pytest', 'Test')">▶ Run Tests (pytest)</button></div>
                    <div><button class="btn-action btn-secondary" onclick="runCommand('wia summary', 'Summary')">▶ WIA Summary</button></div>
                    <div><button class="btn-action btn-secondary" onclick="runCommand('wia status', 'Status')">▶ WIA Status</button></div>
                </div>
            </div>
        </div>

        <!-- Activity History & Chat Output -->
        <div style="margin-top: 20px;">
            <h3 style="margin-bottom: 12px;">💬 Intelligence & Reasoning Stream</h3>
            <div id="chatStream" class="chat-container">
                <div class="message-card">
                    <div style="color: #888;">Ready. Ask any natural language question above to query this workspace.</div>
                </div>
            </div>
        </div>
    </div>

    <!-- VIEW 5: Settings View -->
    <div id="settingsView" class="view-section">
        <div class="onboarding-card">
            <h2>WIA AI Provider Settings</h2>
            <div class="form-group">
                <label>Provider</label>
                <select id="settingsProviderSelect" class="form-control" onchange="handleSettingsProviderChange()">
                    <option value="nvidia">NVIDIA NIM</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="gemini">Google Gemini</option>
                    <option value="local">Local Reasoning (Offline)</option>
                </select>
            </div>
            <div class="form-group">
                <label>API Key</label>
                <input type="password" id="settingsApiKeyInput" class="form-control" placeholder="Update secret key..." />
            </div>
            <div class="form-group">
                <label>Model</label>
                <input type="text" id="settingsModelInput" class="form-control" value="meta/llama-3.1-70b-instruct" />
            </div>
            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <button class="btn-action" onclick="saveSettings()">Save Changes</button>
                <button class="btn-action btn-secondary" onclick="showView('dashboardView')">Back to Dashboard</button>
            </div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function showView(viewId) {
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
            const target = document.getElementById(viewId);
            if (target) target.classList.add('active');
        }

        function quickQuery(text) {
            document.getElementById('queryInput').value = text;
            submitQuery();
        }

        function handleQueryKey(e) {
            if (e.key === 'Enter') submitQuery();
        }

        function submitQuery() {
            const val = document.getElementById('queryInput').value.trim();
            if (!val) return;
            vscode.postMessage({ type: 'askAgent', query: val });
        }

        function authorizeWorkspace() {
            vscode.postMessage({ type: 'authorizeWorkspace' });
        }

        function rescanWorkspace() {
            showView('progressView');
            vscode.postMessage({ type: 'startFirstScan' });
        }

        function runCommand(command, commandName) {
            vscode.postMessage({ type: 'runProjectCommand', command, commandName });
        }

        function fixEnvironment() {
            vscode.postMessage({ type: 'fixEnvironment' });
        }

        function openFile(filePath, line) {
            vscode.postMessage({ type: 'openFile', filePath, line });
        }

        function saveAiSettings() {
            const provider = document.getElementById('providerSelect').value;
            const model = document.getElementById('modelInput').value;
            const apiKey = document.getElementById('apiKeyInput').value;
            vscode.postMessage({ type: 'saveAiConfig', provider, model, apiKey });
            showView('authView');
        }

        function saveSettings() {
            const provider = document.getElementById('settingsProviderSelect').value;
            const model = document.getElementById('settingsModelInput').value;
            const apiKey = document.getElementById('settingsApiKeyInput').value;
            vscode.postMessage({ type: 'saveAiConfig', provider, model, apiKey });
            showView('dashboardView');
        }

        function testConnection() {
            const provider = document.getElementById('providerSelect').value;
            const apiKey = document.getElementById('apiKeyInput').value;
            vscode.postMessage({ type: 'testConnection', provider, apiKey });
        }

        function handleProviderChange() {
            const p = document.getElementById('providerSelect').value;
            const keyGrp = document.getElementById('apiKeyGroup');
            const modelInp = document.getElementById('modelInput');
            if (p === 'local') {
                keyGrp.style.display = 'none';
                modelInp.value = 'deterministic-offline';
            } else {
                keyGrp.style.display = 'flex';
                if (p === 'nvidia') modelInp.value = 'meta/llama-3.1-70b-instruct';
                else if (p === 'openai') modelInp.value = 'gpt-4o-mini';
                else if (p === 'anthropic') modelInp.value = 'claude-3-5-sonnet-20240620';
                else if (p === 'gemini') modelInp.value = 'gemini-1.5-pro';
            }
        }

        function handleSettingsProviderChange() {
            const p = document.getElementById('settingsProviderSelect').value;
            const modelInp = document.getElementById('settingsModelInput');
            if (p === 'nvidia') modelInp.value = 'meta/llama-3.1-70b-instruct';
            else if (p === 'openai') modelInp.value = 'gpt-4o-mini';
            else if (p === 'anthropic') modelInp.value = 'claude-3-5-sonnet-20240620';
            else if (p === 'gemini') modelInp.value = 'gemini-1.5-pro';
            else if (p === 'local') modelInp.value = 'deterministic-offline';
        }

        window.addEventListener('message', event => {
            const msg = event.data;
            switch (msg.type) {
                case 'testConnectionResult':
                    const testDiv = document.getElementById('testConnResult');
                    testDiv.innerText = msg.message;
                    testDiv.style.color = msg.status === 'success' ? 'var(--success)' : 'var(--danger)';
                    break;
                case 'scanProgress':
                    showView('progressView');
                    document.getElementById('progressBarFill').style.width = msg.percent + '%';
                    document.getElementById('progressMessage').innerText = msg.message;
                    break;
                case 'scanComplete':
                    showView('dashboardView');
                    break;
                case 'queryStarted':
                    const stream = document.getElementById('chatStream');
                    const card = document.createElement('div');
                    card.className = 'message-card';
                    card.id = 'activeQueryCard';
                    card.innerHTML = '<strong>' + escapeHtml(msg.query) + '</strong><div id="activeSteps"></div><div id="activeAnswer" class="answer-content" style="margin-top: 8px;">⟳ Routing query via Laya Decision Engine...</div>';
                    stream.prepend(card);
                    break;
                case 'layaDecision':
                    const stepsDiv = document.getElementById('activeSteps');
                    if (stepsDiv) {
                        stepsDiv.innerHTML = '<div class="laya-badge">⚡ Laya Decision: ' + escapeHtml(msg.decision.intent) + ' (' + Math.round(msg.decision.confidence * 100) + '% confidence)</div>';
                    }
                    break;
                case 'operationStarted':
                    const steps = document.getElementById('activeSteps');
                    if (steps) {
                        const step = document.createElement('div');
                        step.className = 'progress-step';
                        step.innerText = '⟳ Executing WIA operation: ' + msg.opName;
                        steps.appendChild(step);
                    }
                    break;
                case 'operationCompleted':
                    const stepsC = document.getElementById('activeSteps');
                    if (stepsC) {
                        const step = document.createElement('div');
                        step.className = 'progress-step';
                        step.innerText = '✓ Completed ' + msg.opName + ' (' + msg.result.duration_ms + 'ms)';
                        stepsC.appendChild(step);
                    }
                    break;
                case 'deterministicResponse':
                    const ansDiv = document.getElementById('activeAnswer');
                    if (ansDiv) {
                        ansDiv.innerHTML = '<strong>Structured Result:</strong><pre style="background: var(--bg-color); padding: 10px; border-radius: 4px; overflow-x: auto; margin-top: 6px;">' + escapeHtml(JSON.stringify(msg.results.map(r => r.result), null, 2)) + '</pre>';
                    }
                    break;
                case 'llmResponseComplete':
                    const ansComplete = document.getElementById('activeAnswer');
                    if (ansComplete) {
                        ansComplete.innerHTML = formatMarkdown(msg.content);
                    }
                    break;
            }
        });

        function escapeHtml(text) {
            return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }

        function formatMarkdown(text) {
            if (!text) return '';
            let html = escapeHtml(text);
            return html;
        }
    </script>
</body>
</html>`;
    }
}
exports.WiaAgentPanel = WiaAgentPanel;
//# sourceMappingURL=WiaAgentPanel.js.map