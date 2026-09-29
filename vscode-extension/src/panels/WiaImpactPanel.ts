import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { WiaApiClient, ImpactResponse } from '../apiClient';
import { WiaExecutor } from '../executor/wiaExecutor';

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
        targetSymbol?: string,
        executor?: WiaExecutor
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

        WiaImpactPanel.currentPanel = new WiaImpactPanel(panel, extensionUri, apiClient, repoId, rootPath, targetSymbol, executor);
    }

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri,
        private apiClient: WiaApiClient,
        private repoId: string | null,
        private rootPath: string | null,
        initialTarget?: string,
        private executor?: WiaExecutor
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

                    const risk = callers.length > 10 ? 'HIGH' : (callers.length > 3 ? 'MEDIUM' : 'LOW');
                    const explanation = callers.length === 0
                        ? `Evidence indicates isolated impact with 0 identified downstream callers or referencing files.`
                        : `Symbol '${target}' is referenced by ${callers.length} downstream caller(s) across ${dependentFiles.size} file(s).`;

                    return {
                        repo_id: 'local',
                        target: target,
                        target_type: targetDef?.symbol_type || 'symbol',
                        risk_level: risk,
                        direct_impact_count: callers.length,
                        direct_impacts: callers.map(c => ({
                            name: c.symbol,
                            symbol_type: 'function',
                            file_path: c.file_path,
                            line: c.line
                        })),
                        affected_files_count: dependentFiles.size,
                        affected_files: Array.from(dependentFiles),
                        explanation: explanation
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

        // 2. Real WIA CLI Impact Execution via Executor
        if (this.executor && this.rootPath) {
            try {
                const res = await this.executor.executeWiaCommand('impact', { symbol: target }, this.rootPath);
                
                // Try JSON parsing first
                let parsedJson: any = null;
                if (res.stdout) {
                    try {
                        const trimmed = res.stdout.trim();
                        if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
                            parsedJson = JSON.parse(trimmed);
                        }
                    } catch (e) {}
                }

                if (parsedJson && (parsedJson.target_symbol || parsedJson.target)) {
                    const directDeps: any[] = parsedJson.direct_dependents || [];
                    const affectedFiles: string[] = parsedJson.affected_files || [];
                    const risk = (parsedJson.risk_level || 'LOW').toUpperCase() as 'HIGH' | 'MEDIUM' | 'LOW';
                    const structuredImpact: ImpactResponse = {
                        repo_id: 'local',
                        target: target,
                        target_type: parsedJson.target_type || 'symbol',
                        risk_level: risk,
                        direct_impact_count: directDeps.length,
                        direct_impacts: directDeps.map((c: string) => {
                            const clean = c.replace(/\s*\([^)]*\)$/, '').trim();
                            const parts = clean.split('::');
                            return {
                                name: parts[1] || parts[0],
                                symbol_type: 'function',
                                file_path: parts[0].trim(),
                                line: 1
                            };
                        }),
                        affected_files_count: affectedFiles.length,
                        affected_files: affectedFiles,
                        explanation: parsedJson.explanation || `Evaluated impact for '${target}' across workspace knowledge graph.`
                    };

                    this._panel.webview.postMessage({
                        command: 'renderImpact',
                        data: structuredImpact,
                        target: target
                    });
                    return;
                }

                if (res.stdout && (res.stdout.includes('Target Entity:') || res.stdout.includes("Impact Analysis for '"))) {
                    const text = res.stdout;
                    
                    const riskMatch = text.match(/Risk Classification:\s*(HIGH|MEDIUM|LOW)/i);
                    const risk = (riskMatch ? riskMatch[1].toUpperCase() : 'LOW') as 'HIGH' | 'MEDIUM' | 'LOW';

                    const explMatch = text.match(/Explanation:\s*([\s\S]*?)(?=\r?\n\r?\n|\r?\n===|$)/);
                    const explanation = explMatch ? explMatch[1].trim() : '';

                    const targetTypeMatch = text.match(/Target Type:\s*(.*)/);
                    const targetType = targetTypeMatch ? targetTypeMatch[1].trim() : 'symbol';

                    function parseSection(headerRegex: RegExp): string[] {
                        const m = text.match(headerRegex);
                        if (!m) return [];
                        const lines = m[1].split(new RegExp('\\r?\\n'));
                        const items: string[] = [];
                        for (const line of lines) {
                            const trimmed = line.trim();
                            if (trimmed.startsWith('*') || trimmed.startsWith('-')) {
                                const item = trimmed.replace(/^[\*\-]\s*/, '').trim();
                                if (item && !item.toLowerCase().startsWith('no ') && !item.includes('additional consuming modules') && !item.includes('additional affected files')) {
                                    items.push(item);
                                }
                            }
                        }
                        return items;
                    }

                    const callersHeaderCountMatch = text.match(/===\s*(?:Direct Symbol Callers|File-Level Dependents)\s*\((\d+)[^)]*\)\s*===/i);
                    const affectedHeaderCountMatch = text.match(/===\s*Affected Files\s*\((\d+)\)\s*===/i);

                    const callers = parseSection(/(?:=== Direct Symbol Callers[^=]*===|=== File-Level Dependents[^=]*===|Direct Symbol Callers:|File-Level Dependents[^:\n]*:)\s*([\s\S]*?)(?=\r?\n===|\r?\n[A-Z][a-zA-Z\s\-]+(?:\(\d+\))?:|$)/);
                    const affected = parseSection(/(?:=== Affected Files[^=]*===|Affected Files[^:\n]*:)\s*([\s\S]*?)(?=\r?\n===|\r?\n[A-Z][a-zA-Z\s\-]+(?:\(\d+\))?:|$)/);

                    const directCount = callersHeaderCountMatch ? parseInt(callersHeaderCountMatch[1], 10) : callers.length;
                    const affectedCount = affectedHeaderCountMatch ? parseInt(affectedHeaderCountMatch[1], 10) : affected.length;

                    const structuredImpact: ImpactResponse = {
                        repo_id: 'local',
                        target: target,
                        target_type: targetType,
                        risk_level: risk,
                        direct_impact_count: directCount,
                        direct_impacts: callers.map(c => {
                            const clean = c.replace(/\s*\(.*\)$/, '').trim();
                            const parts = clean.split('::');
                            return {
                                name: parts[1] || parts[0],
                                symbol_type: 'function',
                                file_path: parts[0].trim(),
                                line: 1
                            };
                        }),
                        affected_files_count: affectedCount,
                        affected_files: affected,
                        explanation: explanation || `Evaluated impact for '${target}' across workspace knowledge graph.`
                    };

                    this._panel.webview.postMessage({
                        command: 'renderImpact',
                        data: structuredImpact,
                        target: target
                    });
                    return;
                }
            } catch (cliErr) {}
        }

        // 3. Fallback from index.json
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
            message: `Symbol '${target}' not found in index. Run "WIA: Scan Workspace" first.`
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
        const nonce = this.getNonce();
        const cspSource = this._panel.webview.cspSource;
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'unsafe-inline'; font-src ${cspSource} data:; img-src ${cspSource} https: data: blob:; script-src 'nonce-${nonce}' ${cspSource};">
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
        <input type="text" id="targetInput" placeholder="Enter symbol name (e.g. hash_file, cli_entrypoint) or file path..." />
        <button class="btn-primary" id="btnAnalyze" type="button">Analyze Impact</button>
    </div>

    <div id="contentArea">
        <div class="empty-state">
            <p>🔍 Enter any class, function, or file path above to calculate caller ripples, downstream importers, and change risk.</p>
        </div>
    </div>

    <script nonce="${nonce}">
        (function() {
            var vscode;
            try {
                if (typeof acquireVsCodeApi === 'function') {
                    vscode = acquireVsCodeApi();
                }
            } catch (e) {
                console.warn('VSCode API acquisition error or already acquired:', e);
            }
            if (!vscode && window.vscode) {
                vscode = window.vscode;
            }
            window.vscode = vscode;

            function postToExtension(msg) {
                try {
                    var api = vscode || window.vscode;
                    if (api && typeof api.postMessage === 'function') {
                        api.postMessage(msg);
                    } else {
                        console.warn('VSCode API unavailable:', msg);
                    }
                } catch (err) {
                    console.error('postToExtension error:', err);
                }
            }

            function searchTarget() {
                var input = document.getElementById('targetInput');
                if (!input) return;
                var target = (input.value || '').trim();
                if (!target) return;
                postToExtension({ command: 'inspectTarget', target: target });
            }

            function openFile(filePath, line) {
                postToExtension({ command: 'openFile', filePath: filePath, line: line });
            }

            function traceFlow(symbol) {
                postToExtension({ command: 'traceFlow', symbol: symbol });
            }

            function attachEventListeners() {
                var btnAnalyze = document.getElementById('btnAnalyze');
                if (btnAnalyze) {
                    btnAnalyze.addEventListener('click', function(e) {
                        e.preventDefault();
                        searchTarget();
                    });
                }

                var targetInput = document.getElementById('targetInput');
                if (targetInput) {
                    targetInput.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            searchTarget();
                        }
                    });
                }
            }

            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', attachEventListeners);
            } else {
                attachEventListeners();
            }

            // Global event delegation
            document.addEventListener('click', function(e) {
                var target = e.target;
                if (!target) return;

                if (target.id === 'btnAnalyze' || target.classList.contains('btn-primary') || target.closest('#btnAnalyze, .btn-primary')) {
                    e.preventDefault();
                    searchTarget();
                    return;
                }

                var openBtn = target.closest('[data-openfile]');
                if (openBtn) {
                    e.preventDefault();
                    var fp = openBtn.getAttribute('data-openfile');
                    var ln = parseInt(openBtn.getAttribute('data-line') || '1', 10);
                    if (fp) openFile(fp, ln);
                    return;
                }

                var traceBtn = target.closest('[data-tracesymbol]');
                if (traceBtn) {
                    e.preventDefault();
                    var sym = traceBtn.getAttribute('data-tracesymbol');
                    if (sym) traceFlow(sym);
                    return;
                }
            }, true);

            window.addEventListener('message', function(event) {
                var msg = event.data;
                if (!msg) return;
                var area = document.getElementById('contentArea');
                if (!area) return;

                if (msg.command === 'setLoading') {
                    area.innerHTML = '<div class="empty-state"><div class="spinner"></div><p style="margin-top:10px;">Analyzing change impact for <b>' + msg.target + '</b> across Knowledge Graph...</p></div>';
                } else if (msg.command === 'showError') {
                    area.innerHTML = '<div class="explanation-box" style="border-left-color:#f85149; background:rgba(248,81,73,0.1);">' + msg.message + '</div>';
                } else if (msg.command === 'renderImpact') {
                    var data = msg.data;
                    var risk = data.risk_level || 'LOW';

                    var html = '';
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
                    if (data.direct_impacts && data.direct_impacts.length > 0) {
                        html += '<div class="section-title">🔗 Direct Callers & Dependents (' + data.direct_impacts.length + ')</div>';
                        html += '<div class="item-list">';
                        data.direct_impacts.forEach(function(item) {
                            html += '<div class="item-card">';
                            html += '  <div class="item-info">';
                            html += '    <span class="item-name">' + (item.name || item.symbol_name || 'Dependent') + ' (' + (item.symbol_type || 'caller') + ')</span>';
                            html += '    <span class="item-path">' + item.file_path + (item.line ? ':' + item.line : '') + '</span>';
                            html += '  </div>';
                            html += '  <div class="item-action">';
                            if (item.name) {
                                html += '    <button class="btn-sm" type="button" data-tracesymbol="' + item.name + '">Trace Flow</button>';
                            }
                            html += '    <button class="btn-sm" type="button" data-openfile="' + item.file_path + '" data-line="' + (item.line || 1) + '">Open File</button>';
                            html += '  </div>';
                            html += '</div>';
                        });
                        html += '</div>';
                    }

                    // Affected Files
                    if (data.affected_files && data.affected_files.length > 0) {
                        html += '<div class="section-title">📁 Ripple Impacted Files (' + data.affected_files.length + ')</div>';
                        html += '<div class="item-list">';
                        data.affected_files.forEach(function(file) {
                            html += '<div class="item-card">';
                            html += '  <span class="item-path">' + file + '</span>';
                            html += '  <button class="btn-sm" type="button" data-openfile="' + file + '" data-line="1">Jump to Source</button>';
                            html += '</div>';
                        });
                        html += '</div>';
                    }

                    area.innerHTML = html;
                }
            });
        })();
    </script>
</body>
</html>`;
    }

    private getNonce(): string {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }
}
