"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SymbolsTreeProvider = exports.SymbolTreeItem = void 0;
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
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
    getLocalSymbols() {
        if (!this.rootPath)
            return [];
        const candidates = [
            path.join(this.rootPath, '.wia', 'index.json'),
            path.join(this.rootPath, 'Workspace-Intelligence-Agent', '.wia', 'index.json')
        ];
        for (const cand of candidates) {
            if (fs.existsSync(cand)) {
                try {
                    const idx = JSON.parse(fs.readFileSync(cand, 'utf8'));
                    const symbols = [];
                    for (const [relPath, fileObj] of Object.entries(idx.files || {})) {
                        const fileSyms = fileObj.extra_metadata?.symbols || [];
                        for (const s of fileSyms) {
                            symbols.push({
                                name: s.name,
                                symbol_type: s.symbol_type || 'function',
                                file_path: relPath,
                                start_line: s.start_line || 1,
                                signature: s.signature || s.name
                            });
                        }
                    }
                    return symbols;
                }
                catch (e) { }
            }
        }
        return [];
    }
    async getChildren(element) {
        let symbols = [];
        // 1. Try API Client
        if (this.repoId) {
            try {
                const res = await this.apiClient.searchSymbols(this.repoId, '');
                symbols = res.symbols || [];
            }
            catch (e) { }
        }
        // 2. Fallback to Local Index
        if (symbols.length === 0) {
            symbols = this.getLocalSymbols();
        }
        if (symbols.length === 0) {
            return [new SymbolTreeItem('Run "WIA: Scan Workspace" to index AST symbols', vscode.TreeItemCollapsibleState.None)];
        }
        const functions = symbols.filter((s) => s.symbol_type === 'function' || s.symbol_type === 'method');
        const classes = symbols.filter((s) => s.symbol_type === 'class');
        const imports = symbols.filter((s) => s.symbol_type === 'import' || s.symbol_type === 'variable');
        if (!element) {
            return [
                new SymbolTreeItem(`Functions & Methods (${functions.length})`, vscode.TreeItemCollapsibleState.Expanded),
                new SymbolTreeItem(`Classes (${classes.length})`, vscode.TreeItemCollapsibleState.Collapsed),
                new SymbolTreeItem(`Imports & Declarations (${imports.length})`, vscode.TreeItemCollapsibleState.Collapsed)
            ];
        }
        let filtered = [];
        if (element.label.startsWith('Functions')) {
            filtered = functions;
        }
        else if (element.label.startsWith('Classes')) {
            filtered = classes;
        }
        else if (element.label.startsWith('Imports')) {
            filtered = imports;
        }
        return filtered.slice(0, 50).map((s) => {
            const fullPath = this.rootPath ? path.join(this.rootPath, s.file_path) : s.file_path;
            return new SymbolTreeItem(s.name, vscode.TreeItemCollapsibleState.None, `${path.basename(s.file_path)}:${s.start_line}`, `${s.signature || s.name}\n${s.file_path}:${s.start_line}`, fullPath, s.start_line);
        });
    }
}
exports.SymbolsTreeProvider = SymbolsTreeProvider;
//# sourceMappingURL=symbolsProvider.js.map