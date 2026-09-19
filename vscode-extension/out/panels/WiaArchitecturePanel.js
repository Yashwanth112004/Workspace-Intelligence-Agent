"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaArchitecturePanel = void 0;
const vscode = require("vscode");
class WiaArchitecturePanel {
    apiClient;
    repoId;
    rootPath;
    static currentPanel;
    _panel;
    _extensionUri;
    _disposables = [];
    static createOrShow(extensionUri, apiClient, repoId, rootPath) {
        const column = vscode.window.activeTextEditor ? vscode.window.activeTextEditor.viewColumn : undefined;
        if (WiaArchitecturePanel.currentPanel) {
            WiaArchitecturePanel.currentPanel._panel.reveal(column);
            WiaArchitecturePanel.currentPanel.loadArchitecture();
            return;
        }
        const panel = vscode.window.createWebviewPanel('wiaArchitecture', '🏛️ WIA Architecture & Subsystem Visualizer', column || vscode.ViewColumn.Beside, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        WiaArchitecturePanel.currentPanel = new WiaArchitecturePanel(panel, extensionUri, apiClient, repoId, rootPath);
    }
    constructor(panel, extensionUri, apiClient, repoId, rootPath) {
        this.apiClient = apiClient;
        this.repoId = repoId;
        this.rootPath = rootPath;
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'refresh':
                    await this.loadArchitecture();
                    return;
                case 'openFile':
                    this.openFile(message.filePath);
                    return;
                case 'askAI':
                    vscode.commands.executeCommand('wia.openChat');
                    return;
            }
        }, null, this._disposables);
        this._panel.webview.html = this._getInitialHtml();
        this.loadArchitecture();
    }
    async loadArchitecture() {
        if (!this.repoId) {
            this._panel.webview.postMessage({
                command: 'showError',
                message: 'No workspace indexed yet. Run the "WIA: Scan Workspace" command to generate architectural intelligence.'
            });
            return;
        }
        this._panel.webview.postMessage({ command: 'setLoading' });
        try {
            const arch = await this.apiClient.getArchitecture(this.repoId);
            const status = await this.apiClient.getStatus(this.repoId);
            this._panel.webview.postMessage({
                command: 'renderArchitecture',
                arch: arch,
                status: status
            });
        }
        catch (e) {
            this._panel.webview.postMessage({
                command: 'showError',
                message: `Failed to load architecture data: ${e.message}`
            });
        }
    }
    openFile(relPath) {
        if (!this.rootPath || !relPath)
            return;
        const normalized = relPath.replace(/^[/\\]+/, '');
        const fullPath = vscode.Uri.file(`${this.rootPath}/${normalized}`);
        vscode.window.showTextDocument(fullPath);
    }
    dispose() {
        WiaArchitecturePanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x)
                x.dispose();
        }
    }
    _getInitialHtml() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIA Architecture Visualizer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            padding: 20px;
            color: var(--vscode-editor-foreground);
            background-color: var(--vscode-editor-background);
            line-height: 1.5;
            margin: 0;
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 14px;
            margin-bottom: 20px;
        }
        .header h2 { margin: 0; font-size: 18px; font-weight: 600; }
        .btn-refresh {
            padding: 6px 12px;
            border-radius: 4px;
            border: 1px solid var(--vscode-panel-border);
            background: var(--vscode-button-secondaryBackground, transparent);
            color: var(--vscode-button-secondaryForeground, inherit);
            cursor: pointer;
            font-size: 12px;
        }
        .btn-refresh:hover { background: var(--vscode-button-background); color: var(--vscode-button-foreground); }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: var(--vscode-sideBar-background, rgba(255, 255, 255, 0.04));
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        .stat-val { font-size: 22px; font-weight: bold; color: var(--vscode-button-background); }
        .stat-label { font-size: 11px; opacity: 0.8; margin-top: 4px; }
        .section-title {
            font-size: 15px;
            font-weight: 600;
            margin: 22px 0 12px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .subsystem-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 14px;
            margin-bottom: 24px;
        }
        .subsystem-card {
            background: var(--vscode-sideBar-background, rgba(255, 255, 255, 0.03));
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 14px;
            transition: border-color 0.2s;
        }
        .subsystem-card:hover { border-color: var(--vscode-focusBorder); }
        .subsystem-name { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
        .subsystem-role { font-size: 12px; opacity: 0.85; margin-bottom: 10px; min-height: 32px; }
        .subsystem-meta {
            display: flex;
            gap: 10px;
            font-size: 11px;
            opacity: 0.7;
            border-top: 1px dashed var(--vscode-panel-border);
            padding-top: 8px;
        }
        .cycle-warning {
            background: rgba(248, 81, 73, 0.1);
            border: 1px solid #f85149;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 20px;
        }
        .cycle-warning h4 { margin: 0 0 8px 0; color: #f85149; font-size: 14px; }
        .cycle-chain { font-family: monospace; font-size: 12px; background: rgba(0,0,0,0.2); padding: 6px 10px; border-radius: 4px; margin-top: 6px; }
        .tag {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(56, 139, 253, 0.15);
            color: #58a6ff;
            font-size: 11px;
            margin-right: 6px;
            margin-bottom: 6px;
        }
        .empty-state { text-align: center; padding: 40px 20px; opacity: 0.7; }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: var(--vscode-button-background);
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="header">
        <h2>🏛️ Architecture & Subsystem Visualizer</h2>
        <button class="btn-refresh" onclick="refresh()">↻ Refresh</button>
    </div>

    <div id="contentArea">
        <div class="empty-state">
            <div class="spinner"></div>
            <p style="margin-top:12px;">Synthesizing workspace architecture & knowledge model...</p>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function refresh() {
            vscode.postMessage({ command: 'refresh' });
        }

        function openFile(filePath) {
            vscode.postMessage({ command: 'openFile', filePath: filePath });
        }

        window.addEventListener('message', event => {
            const msg = event.data;
            const area = document.getElementById('contentArea');

            if (msg.command === 'setLoading') {
                area.innerHTML = '<div class="empty-state"><div class="spinner"></div><p style="margin-top:12px;">Loading architecture graph...</p></div>';
            } else if (msg.command === 'showError') {
                area.innerHTML = '<div style="background:rgba(248,81,73,0.1); border-left:3px solid #f85149; padding:14px; border-radius:4px;">' + msg.message + '</div>';
            } else if (msg.command === 'renderArchitecture') {
                const arch = msg.arch || {};
                const status = msg.status || {};
                let html = '';

                // Stats overview
                html += '<div class="stat-grid">';
                html += '  <div class="stat-card"><div class="stat-val">' + (status.total_files || arch.total_nodes || 0) + '</div><div class="stat-label">Total Files</div></div>';
                html += '  <div class="stat-card"><div class="stat-val">' + (status.total_loc || 0) + '</div><div class="stat-label">Lines of Code</div></div>';
                html += '  <div class="stat-card"><div class="stat-val">' + (arch.total_nodes || 0) + '</div><div class="stat-label">Graph Nodes</div></div>';
                html += '  <div class="stat-card"><div class="stat-val">' + (arch.total_edges || 0) + '</div><div class="stat-label">Relation Edges</div></div>';
                html += '</div>';

                // Circular dependency warnings
                if (arch.circular_dependencies && arch.circular_dependencies.length > 0) {
                    html += '<div class="cycle-warning">';
                    html += '  <h4>⚠️ Circular Dependency Cycles Detected (' + arch.circular_dependencies.length + ')</h4>';
                    html += '  <p style="font-size:12px; margin:0 0 6px 0;">The following files have recursive import cycles detected via DFS cycle detection:</p>';
                    arch.circular_dependencies.forEach(c => {
                        html += '<div class="cycle-chain">🔁 ' + c + '</div>';
                    });
                    html += '</div>';
                }

                // Subsystems
                if (arch.subsystems && arch.subsystems.length > 0) {
                    html += '<div class="section-title">🧱 Subsystem Architecture Boundaries (' + arch.subsystems.length + ')</div>';
                    html += '<div class="subsystem-grid">';
                    arch.subsystems.forEach(s => {
                        html += '<div class="subsystem-card">';
                        html += '  <div class="subsystem-name">' + s.name + '</div>';
                        html += '  <div class="subsystem-role">' + s.role + '</div>';
                        html += '  <div class="subsystem-meta">';
                        html += '    <span>📁 ' + s.file_count + ' files</span>';
                        html += '    <span>⚡ ' + s.symbol_count + ' symbols</span>';
                        html += '  </div>';
                        html += '</div>';
                    });
                    html += '</div>';
                }

                // Entry Points & Frameworks
                html += '<div class="section-title">🚀 Entry Points & Discovered Tech Stack</div>';
                html += '<div style="margin-bottom:20px;">';
                if (status.entry_points && status.entry_points.length > 0) {
                    status.entry_points.forEach(ep => {
                        html += '<span class="tag" style="background:rgba(63,185,80,0.15); color:#3fb950; cursor:pointer;" onclick="openFile(\'' + ep + '\')">🎯 ' + ep + '</span>';
                    });
                }
                if (status.tech_stack) {
                    Object.entries(status.tech_stack).forEach(([lang, loc]) => {
                        html += '<span class="tag">💻 ' + lang + ': ' + loc + ' LOC</span>';
                    });
                }
                html += '</div>';

                area.innerHTML = html;
            }
        });
    </script>
</body>
</html>`;
    }
}
exports.WiaArchitecturePanel = WiaArchitecturePanel;
//# sourceMappingURL=WiaArchitecturePanel.js.map