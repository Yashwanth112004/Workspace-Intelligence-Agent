import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { WiaApiClient } from '../apiClient';

export class DependencyTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly description?: string,
        public readonly tooltip?: string
    ) {
        super(label, collapsibleState);
        this.description = description;
        this.tooltip = tooltip;
    }
}

export class DependenciesTreeProvider implements vscode.TreeDataProvider<DependencyTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<DependencyTreeItem | undefined | null | void> = new vscode.EventEmitter<DependencyTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<DependencyTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private repoId: string | null = null;
    private rootPath: string | null = null;

    constructor(private apiClient: WiaApiClient) {}

    setRepository(repoId: string | null, rootPath?: string | null) {
        this.repoId = repoId;
        if (rootPath !== undefined) {
            this.rootPath = rootPath;
        }
        this.refresh();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: DependencyTreeItem): vscode.TreeItem {
        return element;
    }

    private getLocalDeps(): { manifests: string[]; imports: any[]; conflicts: string[] } {
        const result = { manifests: [] as string[], imports: [] as any[], conflicts: [] as string[] };
        if (!this.rootPath) return result;

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
                        result.conflicts = data.dependency_conflicts.map((c: any) => `${c.package || c.name || 'conflict'}: ${c.message || c.reason || ''}`);
                    }
                    break;
                } catch (e) {}
            }
        }

        return result;
    }

    async getChildren(element?: DependencyTreeItem): Promise<DependencyTreeItem[]> {
        let manifests: string[] = [];
        let imports: any[] = [];
        let conflicts: string[] = [];

        // 1. Try API Client
        if (this.repoId) {
            try {
                const res = await this.apiClient.getDependencies(this.repoId);
                manifests = res.external_dependencies || [];
                imports = res.import_graph || [];
            } catch (e) {}
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
            const items: DependencyTreeItem[] = [];
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
            return conflicts.slice(0, 30).map((c: string) => new DependencyTreeItem(`⚠️ ${c}`, vscode.TreeItemCollapsibleState.None, 'Conflict'));
        }

        if (element.label.startsWith('Package Manifests')) {
            return manifests.map((m: string) => new DependencyTreeItem(`📦 ${m}`, vscode.TreeItemCollapsibleState.None, 'Dependency'));
        }

        if (element.label.startsWith('Import Statements')) {
            return imports.slice(0, 30).map((imp: any) =>
                new DependencyTreeItem(
                    `${imp.source_file} -> ${imp.imported_module}`,
                    vscode.TreeItemCollapsibleState.None,
                    `Line ${imp.line}`
                )
            );
        }

        return [];
    }
}
