import * as vscode from 'vscode';
import { WiaApiClient } from '../apiClient';

export class ArchitectureTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly description?: string,
        public readonly tooltip?: string,
        public readonly filePath?: string,
        public readonly lineNumber?: number
    ) {
        super(label, collapsibleState);
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

export class ArchitectureTreeProvider implements vscode.TreeDataProvider<ArchitectureTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ArchitectureTreeItem | undefined | null | void> = new vscode.EventEmitter<ArchitectureTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ArchitectureTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private repoId: string | null = null;
    private rootPath: string | null = null;

    constructor(private apiClient: WiaApiClient) {}

    setRepository(repoId: string, rootPath: string) {
        this.repoId = repoId;
        this.rootPath = rootPath;
        this.refresh();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ArchitectureTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: ArchitectureTreeItem): Promise<ArchitectureTreeItem[]> {
        if (!this.repoId) {
            return [new ArchitectureTreeItem('Run "WIA: Scan Workspace" to index codebase', vscode.TreeItemCollapsibleState.None)];
        }

        try {
            const arch = await this.apiClient.getArchitecture(this.repoId);
            if (!element) {
                const nodes: ArchitectureTreeItem[] = [];
                nodes.push(new ArchitectureTreeItem(`Architecture Nodes (${arch.total_nodes || 0})`, vscode.TreeItemCollapsibleState.Expanded));
                nodes.push(new ArchitectureTreeItem(`Relationships (${arch.total_edges || 0})`, vscode.TreeItemCollapsibleState.None));
                return nodes;
            }

            if (element.label.startsWith('Architecture Nodes')) {
                return (arch.nodes || []).slice(0, 30).map((n: any) => {
                    const fullPath = this.rootPath && n.file ? `${this.rootPath}/${n.file}` : undefined;
                    return new ArchitectureTreeItem(
                        `[${n.type}] ${n.name}`,
                        vscode.TreeItemCollapsibleState.None,
                        n.file,
                        `${n.name} (${n.type})`,
                        fullPath,
                        0
                    );
                });
            }

            return [];
        } catch (e) {
            return [new ArchitectureTreeItem('Connect to WIA Daemon...', vscode.TreeItemCollapsibleState.None)];
        }
    }
}
