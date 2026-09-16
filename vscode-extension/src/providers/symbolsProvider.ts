import * as vscode from 'vscode';
import { WiaApiClient } from '../apiClient';

export class SymbolTreeItem extends vscode.TreeItem {
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
                title: 'Open Symbol',
                arguments: [
                    vscode.Uri.file(filePath),
                    { selection: new vscode.Range((lineNumber || 1) - 1, 0, (lineNumber || 1) - 1, 0) }
                ]
            };
        }
    }
}

export class SymbolsTreeProvider implements vscode.TreeDataProvider<SymbolTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<SymbolTreeItem | undefined | null | void> = new vscode.EventEmitter<SymbolTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<SymbolTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

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

    getTreeItem(element: SymbolTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: SymbolTreeItem): Promise<SymbolTreeItem[]> {
        if (!this.repoId) {
            return [new SymbolTreeItem('Index workspace to view symbols', vscode.TreeItemCollapsibleState.None)];
        }

        try {
            const res = await this.apiClient.searchSymbols(this.repoId, '');
            const symbols = res.symbols || [];

            if (!element) {
                const functions = symbols.filter((s: any) => s.symbol_type === 'function');
                const classes = symbols.filter((s: any) => s.symbol_type === 'class');
                const imports = symbols.filter((s: any) => s.symbol_type === 'import');

                return [
                    new SymbolTreeItem(`Functions (${functions.length})`, vscode.TreeItemCollapsibleState.Expanded),
                    new SymbolTreeItem(`Classes (${classes.length})`, vscode.TreeItemCollapsibleState.Collapsed),
                    new SymbolTreeItem(`Imports (${imports.length})`, vscode.TreeItemCollapsibleState.Collapsed)
                ];
            }

            let filtered = [];
            if (element.label.startsWith('Functions')) {
                filtered = symbols.filter((s: any) => s.symbol_type === 'function');
            } else if (element.label.startsWith('Classes')) {
                filtered = symbols.filter((s: any) => s.symbol_type === 'class');
            } else if (element.label.startsWith('Imports')) {
                filtered = symbols.filter((s: any) => s.symbol_type === 'import');
            }

            return filtered.slice(0, 40).map((s: any) => {
                const fullPath = this.rootPath ? `${this.rootPath}/${s.file_path}` : s.file_path;
                return new SymbolTreeItem(
                    s.name,
                    vscode.TreeItemCollapsibleState.None,
                    `${s.file_path}:${s.start_line}`,
                    s.signature || s.name,
                    fullPath,
                    s.start_line
                );
            });
        } catch (e) {
            return [new SymbolTreeItem('Waiting for WIA Engine...', vscode.TreeItemCollapsibleState.None)];
        }
    }
}
