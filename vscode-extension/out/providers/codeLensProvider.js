"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaCodeLensProvider = void 0;
const vscode = require("vscode");
class WiaCodeLensProvider {
    apiClient;
    _onDidChangeCodeLenses = new vscode.EventEmitter();
    onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;
    repoId = null;
    rootPath = null;
    constructor(apiClient) {
        this.apiClient = apiClient;
        vscode.workspace.onDidChangeConfiguration(() => {
            this._onDidChangeCodeLenses.fire();
        });
    }
    setRepository(repoId, rootPath) {
        this.repoId = repoId;
        this.rootPath = rootPath;
        this._onDidChangeCodeLenses.fire();
    }
    refresh() {
        this._onDidChangeCodeLenses.fire();
    }
    provideCodeLenses(document, _token) {
        const config = vscode.workspace.getConfiguration('wia');
        if (!config.get('enableCodeLens', true)) {
            return [];
        }
        const codeLenses = [];
        const text = document.getText();
        const lines = text.split(/\r?\n/);
        // Regex patterns for function and class definitions across Python, JS/TS, Go
        const patterns = [
            // Python: def foo(...) or class Bar(...)
            { regex: /^(?:[ \t]*)(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(/, type: 'function' },
            { regex: /^(?:[ \t]*)class\s+([a-zA-Z0-9_]+)\s*[:\(]/, type: 'class' },
            // JS / TS: function foo, class Bar, const foo = () =>
            { regex: /^(?:[ \t]*)(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(/, type: 'function' },
            { regex: /^(?:[ \t]*)(?:export\s+)?class\s+([a-zA-Z0-9_]+)/, type: 'class' },
            { regex: /^(?:[ \t]*)(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>/, type: 'function' },
            // Go: func Foo(...)
            { regex: /^(?:[ \t]*)func\s+(?:\([^)]+\)\s+)?([a-zA-Z0-9_]+)\s*\(/, type: 'function' }
        ];
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            for (const { regex, type } of patterns) {
                const match = line.match(regex);
                if (match && match[1]) {
                    const symbolName = match[1];
                    // Skip private/dunder methods or trivial names
                    if (symbolName.startsWith('__') && symbolName.endsWith('__')) {
                        continue;
                    }
                    const range = new vscode.Range(i, 0, i, line.length);
                    // CodeLens 1: Symbol Refactoring Impact
                    const impactLens = new vscode.CodeLens(range, {
                        title: `⚡ WIA Impact (${symbolName})`,
                        tooltip: `Analyze callers, file importers, and refactoring change risk for '${symbolName}'`,
                        command: 'wia.analyzeImpactForSymbol',
                        arguments: [symbolName, document.uri.fsPath, i + 1]
                    });
                    codeLenses.push(impactLens);
                    // CodeLens 2: Trace Execution Flow
                    const flowLens = new vscode.CodeLens(range, {
                        title: `🔍 Trace Flow`,
                        tooltip: `Trace execution call chain starting at '${symbolName}'`,
                        command: 'wia.traceFlowForSymbol',
                        arguments: [symbolName]
                    });
                    codeLenses.push(flowLens);
                    break;
                }
            }
        }
        return codeLenses;
    }
}
exports.WiaCodeLensProvider = WiaCodeLensProvider;
//# sourceMappingURL=codeLensProvider.js.map