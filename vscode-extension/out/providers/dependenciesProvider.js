"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DependenciesTreeProvider = exports.DependencyTreeItem = void 0;
const vscode = require("vscode");
class DependencyTreeItem extends vscode.TreeItem {
    label;
    collapsibleState;
    description;
    tooltip;
    constructor(label, collapsibleState, description, tooltip) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.description = description;
        this.tooltip = tooltip;
        this.description = description;
        this.tooltip = tooltip;
    }
}
exports.DependencyTreeItem = DependencyTreeItem;
class DependenciesTreeProvider {
    apiClient;
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    repoId = null;
    constructor(apiClient) {
        this.apiClient = apiClient;
    }
    setRepository(repoId) {
        this.repoId = repoId;
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
            return [new DependencyTreeItem('Index workspace to view dependencies', vscode.TreeItemCollapsibleState.None)];
        }
        try {
            const res = await this.apiClient.getDependencies(this.repoId);
            const manifests = res.external_dependencies || [];
            const imports = res.import_graph || [];
            if (!element) {
                return [
                    new DependencyTreeItem(`Package Manifests (${manifests.length})`, vscode.TreeItemCollapsibleState.Expanded),
                    new DependencyTreeItem(`Import Statements (${imports.length})`, vscode.TreeItemCollapsibleState.Collapsed)
                ];
            }
            if (element.label.startsWith('Package Manifests')) {
                return manifests.map((m) => new DependencyTreeItem(m, vscode.TreeItemCollapsibleState.None, 'Manifest'));
            }
            if (element.label.startsWith('Import Statements')) {
                return imports.slice(0, 30).map((imp) => new DependencyTreeItem(`${imp.source_file} -> ${imp.imported_module}`, vscode.TreeItemCollapsibleState.None, `Line ${imp.line}`));
            }
            return [];
        }
        catch (e) {
            return [new DependencyTreeItem('Waiting for WIA Engine...', vscode.TreeItemCollapsibleState.None)];
        }
    }
}
exports.DependenciesTreeProvider = DependenciesTreeProvider;
//# sourceMappingURL=dependenciesProvider.js.map