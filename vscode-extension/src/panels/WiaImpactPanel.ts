import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { WiaApiClient, ImpactResponse } from '../apiClient';

export class WiaImpactPanel {
    public static currentPanel: WiaImpactPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(
        extensionUri: vscode.Uri,
        apiClient: WiaApiClient,
        repoId: string | null,
        rootPath: string | null,
        targetSymbol?: string
    ) {
        const column = vscode.window.activeTextEditor ? vscode.window.activeTextEditor.viewColumn : undefined;

        if (WiaImpactPanel.currentPanel) {
            WiaImpactPanel.currentPanel._panel.reveal(column);
            if (targetSymbol) {
                WiaImpactPanel.currentPanel.loadImpact(targetSymbol);
            }
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'wiaImpact',
            '⚡ WIA Change Impact Inspector',
            column || vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        WiaImpactPanel.currentPanel = new WiaImpactPanel(panel, extensionUri, apiClient, repoId, rootPath, targetSymbol);
    }

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri,
        private apiClient: WiaApiClient,
        private repoId: string | null,
        private rootPath: string | null,
        initialTarget?: string
    ) {
        this._panel = panel;
        this._extensionUri = extensionUri;

        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'inspectTarget':
                        await this.loadImpact(message.target);
                        return;
                    case 'openFile':
                        this.openFileAtLine(message.filePath, message.line);
                        return;
                    case 'traceFlow':
                        vscode.commands.executeCommand('wia.traceFlowForSymbol', message.symbol);
                        return;
                }
            },
            null,
            this._disposables
        );

        this._panel.webview.html = this._getInitialHtml();

        if (initialTarget) {
            this.loadImpact(initialTarget);
        }
    }

    private getLocalSymbolImpact(target: string): ImpactResponse | null {
        if (!this.rootPath) return null;
        const candidates = [
            path.join(this.rootPath, '.wia', 'index.json'),
            path.join(this.rootPath, 'Workspace-Intelligence-Agent', '.wia', 'index.json')
        ];

        for (const cand of candidates) {
            if (fs.existsSync(cand)) {
                try {
                    const idx = JSON.parse(fs.readFileSync(cand, 'utf8'));
                    let targetDef: any = null;
                    const callers: any[] = [];
                    const dependentFiles = new Set<string>();

                    for (const [relPath, fileObj] of Object.entries<any>(idx.files || {})) {
                        const symbols = fileObj.extra_metadata?.symbols || [];
                        for (const s of symbols) {
                            if (s.name.toLowerCase() === target.toLowerCase()) {
                                targetDef = { ...s, file_path: relPath };
                            }
                            if (s.signature && s.signature.includes(target)) {
                                callers.push({
                                    symbol: s.name,
                                    file_path: relPath,
                                    line: s.start_line,
                                    call_type: 'function_call'
                                });
                                dependentFiles.add(relPath);
                            }
                        }
                    }

                    return {
                        repo_id: 'local',
                        target: target,
                        target_type: targetDef?.symbol_type || 'symbol',
                        risk_level: callers.length > 10 ? 'HIGH' : (callers.length > 3 ? 'MEDIUM' : 'LOW'),
                        direct_impact_count: callers.length,
                        direct_impacts: callers.map(c => ({
                            name: c.symbol,
                            symbol_type: 'function',
                            file_path: c.file_path,
                            line: c.line
                        })),
                        affected_files_count: dependentFiles.size,
                        affected_files: Array.from(dependentFiles),
                        explanation: `Symbol '${target}' is referenced by ${callers.length} downstream caller(s) across ${dependentFiles.size} file(s).`
                    };
                } catch (e) {}
            }
        }
        return null;
    }

    public async loadImpact(target: string) {
        this._panel.webview.postMessage({ command: 'setLoading', target });

        // 1. Try API Client
        if (this.repoId) {
            try {
                const data: ImpactResponse = await this.apiClient.analyzeImpact(this.repoId, target);
                this._panel.webview.postMessage({
                    command: 'renderImpact',
                    data: data,
                    target: target
                });
                return;
            } catch (e: any) {}
        }

        // 2. Offline Fallback from index.json
        const local = this.getLocalSymbolImpact(target);
        if (local) {
            this._panel.webview.postMessage({
                command: 'renderImpact',
                data: local,
                target: target
            });
            return;
        }

        this._panel.webview.postMessage({
            command: 'showError',
            message: `No active repository indexed or symbol '${target}' not found. Run "WIA: Scan Workspace" first.`
        });
    }

    private openFileAtLine(relPath: string, line?: number) {
        if (!this.rootPath || !relPath) return;
        const normalized = relPath.replace(/^[/\\]+/, '');
        const fullPath = vscode.Uri.file(path.join(this.rootPath, normalized));
        const targetLine = Math.max(0, (line || 1) - 1);
        vscode.window.showTextDocument(fullPath, {
            selection: new vscode.Range(targetLine, 0, targetLine, 0)
        });
    }

    public dispose() {
        WiaImpactPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) x.dispose();
        }
    }

    private _getInitialHtml(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; script-src * 'unsafe-inline' 'unsafe-eval' vscode-resource:; style-src * 'unsafe-inline'; font-src * data:; img-src * data: blob: vscode-resource:;">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIA Change Impact Inspector</title>
    <style>
        :root {
            --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        body {
            font-family: var(--font-family);
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
            padding-bottom: 14px;
            border-bottom: 1px solid var(--vscode-panel-border);
            margin-bottom: 20px;
        }
        .title-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .title-group h2 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
        }
        .search-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
        }
        input {
            flex: 1;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            font-size: 13px;
        }
        button.btn-primary {
            padding: 8px 16px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
        }
        button.btn-primary:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .risk-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .risk-LOW { background: rgba(63, 185, 80, 0.2); color: #3fb950; border: 1px solid #3fb950; }
        .risk-MEDIUM { background: rgba(210, 153, 34, 0.2); color: #d29922; border: 1px solid #d29922; }
        .risk-HIGH { background: rgba(248, 81, 73, 0.2); color: #f85149; border: 1px solid #f85149; }
        .risk-UNKNOWN, .risk-NOT_FOUND { background: rgba(139, 148, 158, 0.2); color: #8b949e; border: 1px solid #8b949e; }

        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: var(--vscode-sideBar-background, rgba(255, 255, 255, 0.04));
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        .stat-val {
            font-size: 22px;
            font-weight: bold;
            color: var(--vscode-button-background);
        }
        .stat-label {
            font-size: 11px;
            opacity: 0.8;
            margin-top: 4px;
        }
        .section-title {
            font-size: 14px;
            font-weight: 600;
            margin: 18px 0 10px 0;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .item-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 16px;
        }
        .item-card {
            background: var(--vscode-sideBar-background, rgba(255, 255, 255, 0.03));
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .item-card:hover {
            border-color: var(--vscode-focusBorder);
        }
        .item-info {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        .item-name {
            font-weight: 600;
            font-size: 13px;
        }
        .item-path {
            font-size: 11px;
            opacity: 0.75;
            font-family: var(--vscode-editor-font-family, monospace);
        }
        .item-action {
            display: flex;
            gap: 6px;
        }
        .btn-sm {
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid var(--vscode-panel-border);
            background: transparent;
            color: var(--vscode-editor-foreground);
            font-size: 11px;
            cursor: pointer;
        }
        .btn-sm:hover {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        .explanation-box {
            background: rgba(56, 139, 253, 0.1);
            border-left: 3px solid #58a6ff;
            padding: 12px 16px;
            border-radius: 0 6px 6px 0;
            font-size: 13px;
            margin-bottom: 20px;
        }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            opacity: 0.7;
        }
        .spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
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
        <div class="title-group">
            <h2>⚡ Refactoring Change Impact Inspector</h2>
        </div>
    </div>

    <div class="search-bar">
        <input type="text" id="targetInput" placeholder="Enter symbol name (e.g. hash_file, cli_entrypoint) or file path..." onkeydown="if(event.key==='Enter') searchTarget()" />
        <button class="btn-primary" onclick="searchTarget()">Analyze Impact</button>
    </div>

    <div id="contentArea">
        <div class="empty-state">
            <p>🔍 Enter any class, function, or file path above to calculate caller ripples, downstream importers, and change risk.</p>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function searchTarget() {
            const input = document.getElementById('targetInput');
            const target = input.value.trim();
            if (!target) return;
            vscode.postMessage({ command: 'inspectTarget', target: target });
        }

        function openFile(filePath, line) {
            vscode.postMessage({ command: 'openFile', filePath: filePath, line: line });
        }

        function traceFlow(symbol) {
            vscode.postMessage({ command: 'traceFlow', symbol: symbol });
        }

        // Global event delegation
        document.addEventListener('click', function(e) {
            const target = e.target;
            if (!target) return;

            if (target.classList.contains('btn-primary') || target.closest('.btn-primary')) {
                e.preventDefault();
                searchTarget();
                return;
            }

            const openBtn = target.closest('[data-openfile]');
            if (openBtn) {
                e.preventDefault();
                const fp = openBtn.getAttribute('data-openfile');
                const ln = parseInt(openBtn.getAttribute('data-line') || '1', 10);
                if (fp) openFile(fp, ln);
                return;
            }

            const traceBtn = target.closest('[data-tracesymbol]');
            if (traceBtn) {
                e.preventDefault();
                const sym = traceBtn.getAttribute('data-tracesymbol');
                if (sym) traceFlow(sym);
                return;
            }
        });

        window.addEventListener('message', event => {
            const msg = event.data;
            const area = document.getElementById('contentArea');

            if (msg.command === 'setLoading') {
                area.innerHTML = '<div class="empty-state"><div class="spinner"></div><p style="margin-top:10px;">Analyzing change impact for <b>' + msg.target + '</b> across Knowledge Graph...</p></div>';
            } else if (msg.command === 'showError') {
                area.innerHTML = '<div class="explanation-box" style="border-left-color:#f85149; background:rgba(248,81,73,0.1);">' + msg.message + '</div>';
            } else if (msg.command === 'renderImpact') {
                const data = msg.data;
                const risk = data.risk_level || 'LOW';

                let html = '';
                html += '<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">';
                html += '  <h3 style="margin:0; font-size:16px;">Target: <code>' + msg.target + '</code></h3>';
                html += '  <span class="risk-badge risk-' + risk + '">' + risk + ' RISK</span>';
                html += '</div>';

                if (data.explanation) {
                    html += '<div class="explanation-box">' + data.explanation + '</div>';
                }

                html += '<div class="stat-grid">';
                html += '  <div class="stat-card"><div class="stat-val">' + (data.direct_impact_count || 0) + '</div><div class="stat-label">Direct Callers</div></div>';
                html += '  <div class="stat-card"><div class="stat-val">' + (data.affected_files_count || 0) + '</div><div class="stat-label">Affected Files</div></div>';
                html += '  <div class="stat-card"><div class="stat-val">' + risk + '</div><div class="stat-label">Risk Rating</div></div>';
                html += '</div>';

                // Direct Callers
if (data.direct_dependents && data.direct_dependents.length > 0) {                      html += '<div class="section-title">🔗 Direct Callers & Dependents (' + data.direct_dependents.length + ')</div>';
                    html += '<div class="item-list">';
                    data.direct_dependents.forEach(item => {
                        html += '<div class="item-card">';
                        html += '  <div class="item-info">';
                        html += '    <span class="item-name">' + (item.name || item.symbol_name || 'Dependent') + ' (' + (item.symbol_type || 'caller') + ')</span>';
                        html += '    <span class="item-path">' + item.file_path + (item.line ? ':' + item.line : '') + '</span>';
                        html += '  </div>';
                        html += '  <div class="item-action">';
                        if (item.name) {
                            html += '    <button class="btn-sm" onclick="traceFlow(\'' + item.name + '\')">Trace Flow</button>';
                        }
                        html += '    <button class="btn-sm" onclick="openFile(\'' + item.file_path + '\', ' + (item.line || 1) + ')">Open File</button>';
                        html += '  </div>';
                        html += '</div>';
                    });
                    html += '</div>';
                }

                // Affected Files
                if (data.affected_files && data.affected_files.length > 0) {
                    html += '<div class="section-title">📁 Ripple Impacted Files (' + data.affected_files.length + ')</div>';
                    html += '<div class="item-list">';
                    data.affected_files.forEach(file => {
                        html += '<div class="item-card">';
                        html += '  <span class="item-path">' + file + '</span>';
                        html += '  <button class="btn-sm" onclick="openFile(\'' + file + '\', 1)">Jump to Source</button>';
                        html += '</div>';
                    });
                    html += '</div>';
                }

                area.innerHTML = html;
            }
        });
    </script>
</body>
</html>`;
    }
}
