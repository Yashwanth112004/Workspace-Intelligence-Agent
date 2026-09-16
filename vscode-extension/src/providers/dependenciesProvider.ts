import * as vscode from 'vscode';
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

    constructor(private apiClient: WiaApiClient) {}

    setRepository(repoId: string) {
        this.repoId = repoId;
        this.refresh();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: DependencyTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: DependencyTreeItem): Promise<DependencyTreeItem[]> {
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
                return manifests.map((m: string) => new DependencyTreeItem(m, vscode.TreeItemCollapsibleState.None, 'Manifest'));
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
        } catch (e) {
            return [new DependencyTreeItem('Waiting for WIA Engine...', vscode.TreeItemCollapsibleState.None)];
        }
    }
}
