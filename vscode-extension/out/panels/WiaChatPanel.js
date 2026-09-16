"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaChatPanel = void 0;
const vscode = require("vscode");
class WiaChatPanel {
    apiClient;
    repoId;
    rootPath;
    static currentPanel;
    _panel;
    _extensionUri;
    _disposables = [];
    static createOrShow(extensionUri, apiClient, repoId, rootPath) {
        const column = vscode.window.activeTextEditor ? vscode.window.activeTextEditor.viewColumn : undefined;
        if (WiaChatPanel.currentPanel) {
            WiaChatPanel.currentPanel._panel.reveal(column);
            return;
        }
        const panel = vscode.window.createWebviewPanel('wiaChat', '🧠 WIA AI Assistant', column || vscode.ViewColumn.Beside, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        WiaChatPanel.currentPanel = new WiaChatPanel(panel, extensionUri, apiClient, repoId, rootPath);
    }
    constructor(panel, extensionUri, apiClient, repoId, rootPath) {
        this.apiClient = apiClient;
        this.repoId = repoId;
        this.rootPath = rootPath;
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._update();
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'askQuestion':
                    await this.handleUserQuestion(message.text);
                    return;
                case 'openCitation':
                    this.openFileAtLine(message.filePath, message.line);
                    return;
            }
        }, null, this._disposables);
    }
    async handleUserQuestion(text) {
        if (!this.repoId) {
            this._panel.webview.postMessage({
                command: 'addMessage',
                sender: 'assistant',
                text: '❌ Please index the workspace first using the **WIA: Scan Workspace** command.',
                citations: []
            });
            return;
        }
        try {
            const res = await this.apiClient.query(this.repoId, text);
            this._panel.webview.postMessage({
                command: 'addMessage',
                sender: 'assistant',
                text: res.response || 'No response generated.',
                citations: res.citations || []
            });
        }
        catch (e) {
            this._panel.webview.postMessage({
                command: 'addMessage',
                sender: 'assistant',
                text: `❌ Error querying WIA Engine: ${e.message}`,
                citations: []
            });
        }
    }
    openFileAtLine(relPath, line) {
        if (!this.rootPath)
            return;
        const fullPath = vscode.Uri.file(`${this.rootPath}/${relPath}`);
        vscode.window.showTextDocument(fullPath, {
            selection: new vscode.Range(Math.max(0, line - 1), 0, Math.max(0, line - 1), 0)
        });
    }
    dispose() {
        WiaChatPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x)
                x.dispose();
        }
    }
    _update() {
        this._panel.webview.html = this._getHtmlForWebview();
    }
    _getHtmlForWebview() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIA AI Assistant</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 15px; color: var(--vscode-editor-foreground); background-color: var(--vscode-editor-background); display: flex; flex-direction: column; height: 95vh; box-sizing: border-box; }
        .header { display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--vscode-panel-border); padding-bottom: 10px; margin-bottom: 15px; }
        .chat-box { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; margin-bottom: 15px; }
        .msg { padding: 10px 14px; border-radius: 8px; max-width: 85%; line-height: 1.5; font-size: 13px; }
        .msg.user { background: var(--vscode-button-background); color: var(--vscode-button-foreground); align-self: flex-end; }
        .msg.assistant { background: var(--vscode-editor-inactiveSelectionBackground); border: 1px solid var(--vscode-panel-border); align-self: flex-start; }
        .citations { margin-top: 8px; padding-top: 6px; border-top: 1px dashed var(--vscode-panel-border); font-size: 11px; }
        .cite-btn { background: transparent; border: 1px solid var(--vscode-button-background); color: var(--vscode-button-background); padding: 2px 6px; border-radius: 4px; cursor: pointer; margin-right: 4px; margin-top: 4px; }
        .input-bar { display: flex; gap: 8px; }
        input { flex: 1; padding: 8px 12px; border-radius: 4px; border: 1px solid var(--vscode-input-border); background: var(--vscode-input-background); color: var(--vscode-input-foreground); }
        button.send { padding: 8px 16px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🧠 WIA AI Assistant</h2>
    </div>
    <div class="chat-box" id="chat">
        <div class="msg assistant">👋 Hello! I am your <b>Workspace Intelligence Agent</b>. Ask me anything about this codebase, architecture, execution flows, or impact analysis.</div>
    </div>
    <div class="input-bar">
        <input type="text" id="userInput" placeholder="Ask about architecture, functions, flow..." onkeydown="if(event.key==='Enter') sendMsg()" />
        <button class="send" onclick="sendMsg()">Ask</button>
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        function sendMsg() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;
            appendMsg('user', text);
            vscode.postMessage({ command: 'askQuestion', text: text });
            input.value = '';
        }
        function appendMsg(sender, text, citations = []) {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = 'msg ' + sender;
            div.innerHTML = text.replace(/\\n/g, '<br/>');
            if (citations.length > 0) {
                const citeDiv = document.createElement('div');
                citeDiv.className = 'citations';
                citeDiv.innerHTML = '<b>📑 Sources:</b><br/>';
                citations.forEach(c => {
                    const btn = document.createElement('button');
                    btn.className = 'cite-btn';
                    btn.innerText = c.file_path + (c.start_line ? ':' + c.start_line : '');
                    btn.onclick = () => vscode.postMessage({ command: 'openCitation', filePath: c.file_path, line: c.start_line });
                    citeDiv.appendChild(btn);
                });
                div.appendChild(citeDiv);
            }
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
        window.addEventListener('message', event => {
            const msg = event.data;
            if (msg.command === 'addMessage') {
                appendMsg(msg.sender, msg.text, msg.citations);
            }
        });
    </script>
</body>
</html>`;
    }
}
exports.WiaChatPanel = WiaChatPanel;
//# sourceMappingURL=WiaChatPanel.js.map