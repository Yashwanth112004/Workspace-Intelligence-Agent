"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SymbolsTreeProvider = exports.SymbolTreeItem = void 0;
const vscode = require("vscode");
class SymbolTreeItem extends vscode.TreeItem {
    label;
    collapsibleState;
    description;
    tooltip;
    filePath;
    lineNumber;
    constructor(label, collapsibleState, description, tooltip, filePath, lineNumber) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.description = description;
        this.tooltip = tooltip;
        this.filePath = filePath;
        this.lineNumber = lineNumber;
        this.description = description;
        this.tooltip = tooltip;
        if (filePath) {
            this.command = {
                command: 'vscode.open',
                title: 'Open Symbol',
                arguments: [
                    vscode.Uri.file(filePath),
                    { selection: new vscode.Range((lineNumber || 1) - 1, 0, (lineNumber || 1) - 1, 0) }
                ]
            };
        }
    }
}
exports.SymbolTreeItem = SymbolTreeItem;
class SymbolsTreeProvider {
    apiClient;
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    repoId = null;
    rootPath = null;
    constructor(apiClient) {
        this.apiClient = apiClient;
    }
    setRepository(repoId, rootPath) {
        this.repoId = repoId;
        this.rootPath = rootPath;
        this.refresh();
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    async getChildren(element) {
        if (!this.repoId) {
            return [new SymbolTreeItem('Index workspace to view symbols', vscode.TreeItemCollapsibleState.None)];
        }
        try {
            const res = await this.apiClient.searchSymbols(this.repoId, '');
            const symbols = res.symbols || [];
            if (!element) {
                const functions = symbols.filter((s) => s.symbol_type === 'function');
                const classes = symbols.filter((s) => s.symbol_type === 'class');
                const imports = symbols.filter((s) => s.symbol_type === 'import');
                return [
                    new SymbolTreeItem(`Functions (${functions.length})`, vscode.TreeItemCollapsibleState.Expanded),
                    new SymbolTreeItem(`Classes (${classes.length})`, vscode.TreeItemCollapsibleState.Collapsed),
                    new SymbolTreeItem(`Imports (${imports.length})`, vscode.TreeItemCollapsibleState.Collapsed)
                ];
            }
            let filtered = [];
            if (element.label.startsWith('Functions')) {
                filtered = symbols.filter((s) => s.symbol_type === 'function');
            }
            else if (element.label.startsWith('Classes')) {
                filtered = symbols.filter((s) => s.symbol_type === 'class');
            }
            else if (element.label.startsWith('Imports')) {
                filtered = symbols.filter((s) => s.symbol_type === 'import');
            }
            return filtered.slice(0, 40).map((s) => {
                const fullPath = this.rootPath ? `${this.rootPath}/${s.file_path}` : s.file_path;
                return new SymbolTreeItem(s.name, vscode.TreeItemCollapsibleState.None, `${s.file_path}:${s.start_line}`, s.signature || s.name, fullPath, s.start_line);
            });
        }
        catch (e) {
            return [new SymbolTreeItem('Waiting for WIA Engine...', vscode.TreeItemCollapsibleState.None)];
        }
    }
}
exports.SymbolsTreeProvider = SymbolsTreeProvider;
//# sourceMappingURL=symbolsProvider.js.map