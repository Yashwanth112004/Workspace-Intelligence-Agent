import * as vscode from 'vscode';
import { WiaApiClient } from '../apiClient';
import { WiaExecutor } from '../executor/wiaExecutor';

export class WiaChatPanel {
    public static currentPanel: WiaChatPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(
        extensionUri: vscode.Uri,
        apiClient: WiaApiClient,
        repoId: string | null,
        rootPath: string | null,
        initialPrompt?: string,
        executor?: WiaExecutor
    ) {
        const column = vscode.window.activeTextEditor ? vscode.window.activeTextEditor.viewColumn : undefined;

        if (WiaChatPanel.currentPanel) {
            WiaChatPanel.currentPanel._panel.reveal(column);
            if (initialPrompt) {
                WiaChatPanel.currentPanel.handleUserQuestion(initialPrompt);
            }
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'wiaChat',
            '🧠 WIA AI Assistant',
            column || vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        WiaChatPanel.currentPanel = new WiaChatPanel(panel, extensionUri, apiClient, repoId, rootPath, initialPrompt, executor);
    }

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri,
        private apiClient: WiaApiClient,
        private repoId: string | null,
        private rootPath: string | null,
        initialPrompt?: string,
        private executor?: WiaExecutor
    ) {
        this._panel = panel;
        this._extensionUri = extensionUri;

        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'askQuestion':
                        await this.handleUserQuestion(message.text);
                        return;
                    case 'openCitation':
                        this.openFileAtLine(message.filePath, message.line);
                        return;
                    case 'startDaemon':
                        vscode.commands.executeCommand('wia.startDaemon');
                        return;
                    case 'scanWorkspace':
                        vscode.commands.executeCommand('wia.scanWorkspace');
                        return;
                }
            },
            null,
            this._disposables
        );

        this._panel.webview.html = this._getHtmlForWebview();

        if (initialPrompt) {
            this.handleUserQuestion(initialPrompt);
        }
    }

    public setRepository(repoId: string | null, rootPath: string | null) {
        this.repoId = repoId;
        this.rootPath = rootPath;
    }

    public async handleUserQuestion(text: string) {
        if (!text || !text.trim()) return;

        if (!this.repoId) {
            // Check if we can determine root path from workspace
            if (!this.rootPath && vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
                this.rootPath = vscode.workspace.workspaceFolders[0].uri.fsPath;
            }

            if (!this.rootPath) {
                this._panel.webview.postMessage({
                    command: 'addMessage',
                    sender: 'assistant',
                    text: '⚠️ **Workspace Required**: Please open a project workspace folder to query the WIA AI engine.',
                    citations: [],
                    showScanBtn: false
                });
                return;
            }

            this._panel.webview.postMessage({
                command: 'setThinking',
                isThinking: true
            });

            try {
                // Attempt automatic on-demand ingestion/query
                const ingestRes = await this.apiClient.ingest(this.rootPath, 'Workspace');
                this.repoId = ingestRes.repo_id;
            } catch {
                // Fallback to local WIA offline reasoning when daemon is offline
                if (this.executor && this.rootPath) {
                    try {
                        const res = await this.executor.executeWiaCommand('ask', { query: text }, this.rootPath);
                        this._panel.webview.postMessage({
                            command: 'setThinking',
                            isThinking: false
                        });
                        this._panel.webview.postMessage({
                            command: 'addMessage',
                            sender: 'assistant',
                            text: res.stdout || res.stderr || 'No response generated.',
                            citations: []
                        });
                        return;
                    } catch (e: any) {}
                }

                this._panel.webview.postMessage({
                    command: 'setThinking',
                    isThinking: false
                });
                this._panel.webview.postMessage({
                    command: 'addMessage',
                    sender: 'assistant',
                    text: '⚠️ **WIA Daemon Not Connected**: Please start the WIA engine daemon or run **Scan Workspace** to query the AI assistant.',
                    citations: [],
                    showDaemonBtn: true,
                    showScanBtn: true
                });
                return;
            }
        }

        this._panel.webview.postMessage({
            command: 'setThinking',
            isThinking: true
        });

        try {
            const res = await this.apiClient.query(this.repoId, text);
            this._panel.webview.postMessage({
                command: 'setThinking',
                isThinking: false
            });
            this._panel.webview.postMessage({
                command: 'addMessage',
                sender: 'assistant',
                text: res.response || 'No authoritative response could be synthesized.',
                citations: res.citations || [],
                intent: res.intent
            });
        } catch (e: any) {
            this._panel.webview.postMessage({
                command: 'setThinking',
                isThinking: false
            });
            this._panel.webview.postMessage({
                command: 'addMessage',
                sender: 'assistant',
                text: `❌ **WIA Engine Notice**: ${e.message}\n\n*Make sure the local daemon is running, or use the interactive WIA Agent sidebar for offline intelligence.*`,
                citations: [],
                showDaemonBtn: true
            });
        }
    }

    private openFileAtLine(relPath: string, line?: number) {
        if (!this.rootPath || !relPath) return;
        const normalized = relPath.replace(/^[/\\]+/, '');
        const fullPath = vscode.Uri.file(`${this.rootPath}/${normalized}`);
        const targetLine = Math.max(0, (line || 1) - 1);
        vscode.window.showTextDocument(fullPath, {
            selection: new vscode.Range(targetLine, 0, targetLine, 0)
        });
    }

    public dispose() {
        WiaChatPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) x.dispose();
        }
    }

    private _getHtmlForWebview(): string {
        const nonce = this.getNonce();
        const cspSource = this._panel.webview.cspSource;
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'unsafe-inline'; font-src ${cspSource} data:; img-src ${cspSource} https: data: blob:; script-src 'nonce-${nonce}' ${cspSource};">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIA AI Assistant</title>
    <style>
        :root {
            --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        body {
            font-family: var(--font-family);
            padding: 16px;
            color: var(--vscode-editor-foreground);
            background-color: var(--vscode-editor-background);
            display: flex;
            flex-direction: column;
            height: 96vh;
            box-sizing: border-box;
            margin: 0;
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 12px;
            margin-bottom: 12px;
        }
        .header h3 { margin: 0; font-size: 16px; display: flex; align-items: center; gap: 8px; }
        .prompt-chips {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }
        .chip {
            background: var(--vscode-sideBar-background, rgba(255, 255, 255, 0.05));
            border: 1px solid var(--vscode-panel-border);
            border-radius: 14px;
            padding: 4px 10px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.15s;
        }
        .chip:hover {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-color: var(--vscode-button-background);
        }
        .chat-box {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
            margin-bottom: 14px;
            padding-right: 4px;
        }
        .msg {
            padding: 12px 16px;
            border-radius: 8px;
            max-width: 90%;
            line-height: 1.55;
            font-size: 13px;
            word-wrap: break-word;
        }
        .msg.user {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .msg.assistant {
            background: var(--vscode-sideBar-background, rgba(255, 255, 255, 0.04));
            border: 1px solid var(--vscode-panel-border);
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }
        .intent-badge {
            display: inline-block;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(56, 139, 253, 0.2);
            color: #58a6ff;
            margin-bottom: 6px;
            font-family: monospace;
            text-transform: uppercase;
        }
        pre {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--vscode-panel-border);
            padding: 10px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 12px;
            margin: 8px 0;
        }
        code {
            font-family: var(--vscode-editor-font-family, monospace);
            background: rgba(127, 127, 127, 0.15);
            padding: 2px 4px;
            border-radius: 3px;
        }
        pre code { background: transparent; padding: 0; }
        .citations {
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px dashed var(--vscode-panel-border);
            font-size: 11px;
        }
        .cite-btn {
            background: transparent;
            border: 1px solid var(--vscode-button-background);
            color: var(--vscode-button-background);
            padding: 3px 8px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 6px;
            margin-top: 6px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .cite-btn:hover {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        .input-bar {
            display: flex;
            gap: 8px;
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
            border-radius: 6px;
            padding: 4px;
        }
        textarea {
            flex: 1;
            padding: 8px 10px;
            border: none;
            background: transparent;
            color: var(--vscode-input-foreground);
            font-family: inherit;
            font-size: 13px;
            resize: none;
            height: 38px;
            outline: none;
        }
        button.send-btn {
            padding: 8px 16px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        }
        button.send-btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .action-btn {
            margin-top: 8px;
            display: inline-block;
            padding: 6px 12px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .thinking-box {
            display: none;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            opacity: 0.8;
            padding: 8px;
        }
        .spinner {
            width: 14px;
            height: 14px;
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
        <h3>🧠 WIA Workspace AI Agent</h3>
    </div>

    <div class="prompt-chips">
        <span class="chip" data-prompt="Explain the high-level architecture of this repository.">🏛️ Architecture</span>
        <span class="chip" data-prompt="Generate a complete developer onboarding guide for this workspace.">📖 Onboarding Guide</span>
        <span class="chip" data-prompt="Audit codebase health, complexity hotspots, and structural debt.">🩺 Health Audit</span>
        <span class="chip" data-prompt="Which files have the highest incoming dependencies and risk?">⚡ Impact Risks</span>
    </div>

    <div class="chat-box" id="chat">
        <div class="msg assistant">
            👋 <b>Welcome to Workspace Intelligence Agent!</b><br/>
            I can answer technical questions, explain architecture boundaries, trace execution flow, and assess refactoring risk grounded in your codebase knowledge graph.
        </div>
    </div>

    <div class="thinking-box" id="thinkingBox">
        <div class="spinner"></div>
        <span>WIA NOOA Agent is synthesizing codebase facts & knowledge graph...</span>
    </div>

    <div class="input-bar">
        <textarea id="userInput" placeholder="Ask anything about architecture, symbols, flow... (Enter to send)"></textarea>
        <button class="send-btn" id="btnSendChat" type="button">Ask</button>
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

            function sendPrompt(text) {
                var input = document.getElementById('userInput');
                if (input) {
                    input.value = text;
                    sendMsg();
                }
            }

            function sendMsg() {
                var input = document.getElementById('userInput');
                if (!input) return;
                var text = (input.value || '').trim();
                if (!text) return;
                appendMsg('user', text);
                postToExtension({ command: 'askQuestion', text: text });
                input.value = '';
            }

            function triggerScan() {
                postToExtension({ command: 'scanWorkspace' });
            }

            function triggerDaemon() {
                postToExtension({ command: 'startDaemon' });
            }

            function renderMarkdown(md) {
                var html = String(md || '')
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');

                var bt = String.fromCharCode(96);
                // Code blocks
                var cbRegex = new RegExp(bt + '{3}([a-zA-Z0-9_-]*)[\\r\\n]([\\s\\S]*?)' + bt + '{3}', 'g');
                html = html.replace(cbRegex, '<pre><code>$2</code></pre>');
                // Inline code
                html = html.replace(new RegExp(bt + '([^' + bt + ']+)' + bt, 'g'), '<code>$1</code>');
                // Bold
                html = html.replace(new RegExp('\\*\\*([^\\*]+)\\*\\*', 'g'), '<b>$1</b>');
                // Italics
                html = html.replace(new RegExp('\\*([^\\*]+)\\*', 'g'), '<i>$1</i>');
                // Headers
                html = html.replace(new RegExp('^### (.*$)', 'gm'), '<h4 style="margin:8px 0 4px 0;">$1</h4>');
                html = html.replace(new RegExp('^## (.*$)', 'gm'), '<h3 style="margin:10px 0 6px 0;">$1</h3>');
                html = html.replace(new RegExp('^# (.*$)', 'gm'), '<h2 style="margin:12px 0 8px 0;">$1</h2>');
                // Line breaks
                html = html.split(new RegExp('\\r?\\n')).join('<br/>');
                return html;
            }

            function appendMsg(sender, text, citations, intent, showScanBtn, showDaemonBtn) {
                citations = citations || [];
                var chat = document.getElementById('chat');
                if (!chat) return;
                var div = document.createElement('div');
                div.className = 'msg ' + sender;

                var content = '';
                if (intent) {
                    content += '<span class="intent-badge">INTENT: ' + intent + '</span><br/>';
                }
                content += renderMarkdown(text);

                if (showScanBtn) {
                    content += '<br/><button class="action-btn" type="button" data-action="scan">🚀 Scan Workspace Now</button>';
                }
                if (showDaemonBtn) {
                    content += '<br/><button class="action-btn" type="button" data-action="daemon">⚡ Start WIA Daemon</button>';
                }

                if (citations && citations.length > 0) {
                    content += '<div class="citations"><b>📑 Evidence Sources:</b><br/>';
                    citations.forEach(function(c) {
                        var lineSuffix = c.start_line ? ':' + c.start_line : '';
                        var escapedPath = (c.file_path || '').replace(/"/g, '&quot;');
                        var lineNum = c.start_line || 1;
                        content += '<button class="cite-btn" type="button" data-filepath="' + escapedPath + '" data-line="' + lineNum + '">📄 ' + escapedPath + lineSuffix + '</button>';
                    });
                    content += '</div>';
                }

                div.innerHTML = content;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }

            function attachEventListeners() {
                var btnSendChat = document.getElementById('btnSendChat');
                if (btnSendChat) {
                    btnSendChat.addEventListener('click', function(e) {
                        e.preventDefault();
                        sendMsg();
                    });
                }

                var userInput = document.getElementById('userInput');
                if (userInput) {
                    userInput.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            sendMsg();
                        }
                    });
                }
            }

            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', attachEventListeners);
            } else {
                attachEventListeners();
            }

            // Document-wide delegated event handler
            document.addEventListener('click', function(e) {
                var target = e.target;
                if (!target) return;

                // Ask / Send button
                if (target.id === 'btnSendChat' || target.classList.contains('send-btn') || target.closest('#btnSendChat, .send-btn')) {
                    e.preventDefault();
                    sendMsg();
                    return;
                }

                // Prompt chips
                var chip = target.closest('.chip');
                if (chip) {
                    e.preventDefault();
                    var text = chip.getAttribute('data-prompt') || chip.textContent.replace(new RegExp('^[^\\w]+'), '').trim();
                    sendPrompt(text);
                    return;
                }

                // Action buttons
                var actionBtn = target.closest('.action-btn');
                if (actionBtn) {
                    e.preventDefault();
                    var act = actionBtn.getAttribute('data-action');
                    if (act === 'scan' || actionBtn.textContent.includes('Scan Workspace')) {
                        triggerScan();
                    } else if (act === 'daemon' || actionBtn.textContent.includes('Start WIA Daemon')) {
                        triggerDaemon();
                    }
                    return;
                }

                // Citation buttons
                var citeBtn = target.closest('.cite-btn');
                if (citeBtn) {
                    e.preventDefault();
                    var fp = citeBtn.getAttribute('data-filepath');
                    var line = parseInt(citeBtn.getAttribute('data-line') || '1', 10);
                    if (fp) {
                        postToExtension({ command: 'openCitation', filePath: fp, line: line });
                    }
                    return;
                }
            }, true);

            window.addEventListener('message', function(event) {
                var msg = event.data;
                if (!msg) return;
                if (msg.command === 'addMessage') {
                    appendMsg(msg.sender, msg.text, msg.citations, msg.intent, msg.showScanBtn, msg.showDaemonBtn);
                } else if (msg.command === 'setThinking') {
                    var box = document.getElementById('thinkingBox');
                    if (box) box.style.display = msg.isThinking ? 'flex' : 'none';
                    if (msg.isThinking) {
                        var chat = document.getElementById('chat');
                        if (chat) chat.scrollTop = chat.scrollHeight;
                    }
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
