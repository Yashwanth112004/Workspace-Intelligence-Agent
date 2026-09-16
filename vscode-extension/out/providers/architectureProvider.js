"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArchitectureTreeProvider = exports.ArchitectureTreeItem = void 0;
const vscode = require("vscode");
class ArchitectureTreeItem extends vscode.TreeItem {
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
                title: 'Open File',
                arguments: [
                    vscode.Uri.file(filePath),
                    { selection: new vscode.Range(lineNumber || 0, 0, lineNumber || 0, 0) }
                ]
            };
        }
    }
}
exports.ArchitectureTreeItem = ArchitectureTreeItem;
class ArchitectureTreeProvider {
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
            return [new ArchitectureTreeItem('Run "WIA: Scan Workspace" to index codebase', vscode.TreeItemCollapsibleState.None)];
        }
        try {
            const arch = await this.apiClient.getArchitecture(this.repoId);
            if (!element) {
                const nodes = [];
                nodes.push(new ArchitectureTreeItem(`Architecture Nodes (${arch.total_nodes || 0})`, vscode.TreeItemCollapsibleState.Expanded));
                nodes.push(new ArchitectureTreeItem(`Relationships (${arch.total_edges || 0})`, vscode.TreeItemCollapsibleState.None));
                return nodes;
            }
            if (element.label.startsWith('Architecture Nodes')) {
                return (arch.nodes || []).slice(0, 30).map((n) => {
                    const fullPath = this.rootPath && n.file ? `${this.rootPath}/${n.file}` : undefined;
                    return new ArchitectureTreeItem(`[${n.type}] ${n.name}`, vscode.TreeItemCollapsibleState.None, n.file, `${n.name} (${n.type})`, fullPath, 0);
                });
            }
            return [];
        }
        catch (e) {
            return [new ArchitectureTreeItem('Connect to WIA Daemon...', vscode.TreeItemCollapsibleState.None)];
        }
    }
}
exports.ArchitectureTreeProvider = ArchitectureTreeProvider;
//# sourceMappingURL=architectureProvider.js.map