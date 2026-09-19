import * as vscode from 'vscode';
import { WiaApiClient } from '../apiClient';

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
        initialPrompt?: string
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

        WiaChatPanel.currentPanel = new WiaChatPanel(panel, extensionUri, apiClient, repoId, rootPath, initialPrompt);
    }

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri,
        private apiClient: WiaApiClient,
        private repoId: string | null,
        private rootPath: string | null,
        initialPrompt?: string
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
        if (!this.repoId) {
            this._panel.webview.postMessage({
                command: 'addMessage',
                sender: 'assistant',
                text: '⚠️ **Workspace Not Indexed**: Please index this workspace first using **WIA: Scan Workspace** before querying the AI engine.',
                citations: [],
                showScanBtn: true
            });
            return;
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
                text: `❌ **WIA Engine Error**: ${e.message}\n\n*Ensure the local backend daemon is running on port 8000.*`,
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
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
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
        <span class="chip" onclick="sendPrompt('Explain the high-level architecture of this repository.')">🏛️ Architecture</span>
        <span class="chip" onclick="sendPrompt('Generate a complete developer onboarding guide for this workspace.')">📖 Onboarding Guide</span>
        <span class="chip" onclick="sendPrompt('Audit codebase health, complexity hotspots, and structural debt.')">🩺 Health Audit</span>
        <span class="chip" onclick="sendPrompt('Which files have the highest incoming dependencies and risk?')">⚡ Impact Risks</span>
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
        <textarea id="userInput" placeholder="Ask anything about architecture, symbols, flow... (Enter to send)" onkeydown="if(event.key==='Enter' && !event.shiftKey) { event.preventDefault(); sendMsg(); }"></textarea>
        <button class="send-btn" onclick="sendMsg()">Ask</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function sendPrompt(text) {
            document.getElementById('userInput').value = text;
            sendMsg();
        }

        function sendMsg() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;
            appendMsg('user', text);
            vscode.postMessage({ command: 'askQuestion', text: text });
            input.value = '';
        }

        function triggerScan() {
            vscode.postMessage({ command: 'scanWorkspace' });
        }

        function triggerDaemon() {
            vscode.postMessage({ command: 'startDaemon' });
        }

        function renderMarkdown(md) {
            let html = md
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');

            // Code blocks
            html = html.replace(new RegExp('\\x60\\x60\\x60([a-zA-Z0-9_-]*)\\n([\\s\\S]*?)\\x60\\x60\\x60', 'g'), '<pre><code>$2</code></pre>');
            // Inline code
            html = html.replace(new RegExp('\\x60([^\\x60]+)\\x60', 'g'), '<code>$1</code>');
            // Bold
            html = html.replace(/\\*\\*([^\\*]+)\\*\\*/g, '<b>$1</b>');
            // Italics
            html = html.replace(/\\*([^\\*]+)\\*/g, '<i>$1</i>');
            // Headers
            html = html.replace(/^### (.*$)/gim, '<h4 style="margin:8px 0 4px 0;">$1</h4>');
            html = html.replace(/^## (.*$)/gim, '<h3 style="margin:10px 0 6px 0;">$1</h3>');
            html = html.replace(/^# (.*$)/gim, '<h2 style="margin:12px 0 8px 0;">$1</h2>');
            // Line breaks
            html = html.replace(/\\n/g, '<br/>');
            return html;
        }

        function appendMsg(sender, text, citations = [], intent = null, showScanBtn = false, showDaemonBtn = false) {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = 'msg ' + sender;

            let content = '';
            if (intent) {
                content += '<span class="intent-badge">INTENT: ' + intent + '</span><br/>';
            }
            content += renderMarkdown(text);

            if (showScanBtn) {
                content += '<br/><button class="action-btn" onclick="triggerScan()">🚀 Scan Workspace Now</button>';
            }
            if (showDaemonBtn) {
                content += '<br/><button class="action-btn" onclick="triggerDaemon()">⚡ Start WIA Daemon</button>';
            }

            if (citations && citations.length > 0) {
                content += '<div class="citations"><b>📑 Evidence Sources:</b><br/>';
                citations.forEach(c => {
                    const lineSuffix = c.start_line ? ':' + c.start_line : '';
                    content += '<button class="cite-btn" onclick="vscode.postMessage({ command: \\'openCitation\\', filePath: \\'' + c.file_path + '\\', line: ' + (c.start_line || 1) + ' })">📄 ' + c.file_path + lineSuffix + '</button>';
                });
                content += '</div>';
            }

            div.innerHTML = content;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        window.addEventListener('message', event => {
            const msg = event.data;
            if (msg.command === 'addMessage') {
                appendMsg(msg.sender, msg.text, msg.citations, msg.intent, msg.showScanBtn, msg.showDaemonBtn);
            } else if (msg.command === 'setThinking') {
                document.getElementById('thinkingBox').style.display = msg.isThinking ? 'flex' : 'none';
                if (msg.isThinking) {
                    const chat = document.getElementById('chat');
                    chat.scrollTop = chat.scrollHeight;
                }
            }
        });
    </script>
</body>
</html>`;
    }
}
