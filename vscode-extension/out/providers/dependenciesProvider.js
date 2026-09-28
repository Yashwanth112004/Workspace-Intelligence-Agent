"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DependenciesTreeProvider = exports.DependencyTreeItem = void 0;
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
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
    rootPath = null;
    constructor(apiClient) {
        this.apiClient = apiClient;
    }
    setRepository(repoId, rootPath) {
        this.repoId = repoId;
        if (rootPath !== undefined) {
            this.rootPath = rootPath;
        }
        this.refresh();
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getLocalDeps() {
        const result = { manifests: [], imports: [], conflicts: [] };
        if (!this.rootPath)
            return result;
        const candidates = [
            path.join(this.rootPath, '.wia', 'report_data.json'),
            path.join(this.rootPath, 'Workspace-Intelligence-Agent', '.wia', 'report_data.json')
        ];
        for (const cand of candidates) {
            if (fs.existsSync(cand)) {
                try {
                    const data = JSON.parse(fs.readFileSync(cand, 'utf8'));
                    if (data.frameworks) {
                        result.manifests = data.frameworks;
                    }
                    if (data.dependency_conflicts) {
                        result.conflicts = data.dependency_conflicts.map((c) => `${c.package || c.name || 'conflict'}: ${c.message || c.reason || ''}`);
                    }
                    break;
                }
                catch (e) { }
            }
        }
        return result;
    }
    async getChildren(element) {
        let manifests = [];
        let imports = [];
        let conflicts = [];
        // 1. Try API Client
        if (this.repoId) {
            try {
                const res = await this.apiClient.getDependencies(this.repoId);
                manifests = res.external_dependencies || [];
                imports = res.import_graph || [];
            }
            catch (e) { }
        }
        // 2. Fallback to Local Report
        if (manifests.length === 0 && imports.length === 0) {
            const local = this.getLocalDeps();
            manifests = local.manifests;
            conflicts = local.conflicts;
        }
        if (manifests.length === 0 && imports.length === 0 && conflicts.length === 0) {
            return [new DependencyTreeItem('Run "WIA: Scan Workspace" to view dependencies', vscode.TreeItemCollapsibleState.None)];
        }
        if (!element) {
            const items = [];
            if (conflicts.length > 0) {
                items.push(new DependencyTreeItem(`⚠️ Conflicts & Warnings (${conflicts.length})`, vscode.TreeItemCollapsibleState.Expanded, 'Needs Resolution'));
            }
            items.push(new DependencyTreeItem(`Package Manifests & Ecosystems (${manifests.length})`, vscode.TreeItemCollapsibleState.Expanded));
            if (imports.length > 0) {
                items.push(new DependencyTreeItem(`Import Statements (${imports.length})`, vscode.TreeItemCollapsibleState.Collapsed));
            }
            return items;
        }
        if (element.label.startsWith('⚠️ Conflicts')) {
            return conflicts.slice(0, 30).map((c) => new DependencyTreeItem(`⚠️ ${c}`, vscode.TreeItemCollapsibleState.None, 'Conflict'));
        }
        if (element.label.startsWith('Package Manifests')) {
            return manifests.map((m) => new DependencyTreeItem(`📦 ${m}`, vscode.TreeItemCollapsibleState.None, 'Dependency'));
        }
        if (element.label.startsWith('Import Statements')) {
            return imports.slice(0, 30).map((imp) => new DependencyTreeItem(`${imp.source_file} -> ${imp.imported_module}`, vscode.TreeItemCollapsibleState.None, `Line ${imp.line}`));
        }
        return [];
    }
}
exports.DependenciesTreeProvider = DependenciesTreeProvider;
//# sourceMappingURL=dependenciesProvider.js.map