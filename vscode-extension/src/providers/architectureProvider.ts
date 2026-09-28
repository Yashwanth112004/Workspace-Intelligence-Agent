import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
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

    setRepository(repoId: string | null, rootPath: string | null) {
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

    private getLocalReportData(): any {
        if (!this.rootPath) return null;
        const candidates = [
            path.join(this.rootPath, '.wia', 'report_data.json'),
            path.join(this.rootPath, 'Workspace-Intelligence-Agent', '.wia', 'report_data.json')
        ];
        for (const cand of candidates) {
            if (fs.existsSync(cand)) {
                try {
                    return JSON.parse(fs.readFileSync(cand, 'utf8'));
                } catch (e) {}
            }
        }
        return null;
    }

    async getChildren(element?: ArchitectureTreeItem): Promise<ArchitectureTreeItem[]> {
        const localData = this.getLocalReportData();

        // 1. Try API Client if repoId is available
        if (this.repoId) {
            try {
                const arch = await this.apiClient.getArchitecture(this.repoId);
                if (!element) {
                    const nodes: ArchitectureTreeItem[] = [];
                    nodes.push(new ArchitectureTreeItem(`Architecture Nodes (${arch.total_nodes || 0})`, vscode.TreeItemCollapsibleState.Expanded));
                    nodes.push(new ArchitectureTreeItem(`Relationships (${arch.total_edges || 0})`, vscode.TreeItemCollapsibleState.None));
                    return nodes;
                }

                if (element.label.startsWith('Architecture Nodes')) {
                    return (arch.nodes || []).slice(0, 50).map((n: any) => {
                        const fullPath = this.rootPath && n.file ? path.join(this.rootPath, n.file) : undefined;
                        return new ArchitectureTreeItem(
                            `[${n.type || 'module'}] ${n.name}`,
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
                // Fallback to local report data below
            }
        }

        // 2. Offline Fallback from .wia/report_data.json
        if (localData) {
            const stats = localData.stats || {};
            const frameworks = localData.frameworks || [];
            const languages = Object.keys(localData.languages || {});

            if (!element) {
                return [
                    new ArchitectureTreeItem(`Indexed Files (${stats.total_indexed || 0})`, vscode.TreeItemCollapsibleState.Collapsed, 'Local Index'),
                    new ArchitectureTreeItem(`Frameworks (${frameworks.length})`, vscode.TreeItemCollapsibleState.Expanded, frameworks.slice(0, 3).join(', ')),
                    new ArchitectureTreeItem(`Languages (${languages.length})`, vscode.TreeItemCollapsibleState.Collapsed, languages.slice(0, 3).join(', ')),
                    new ArchitectureTreeItem(`Dependencies (${stats.dependencies_count || 0})`, vscode.TreeItemCollapsibleState.None, `${stats.dependency_conflicts_count || 0} conflicts`)
                ];
            }

            if (element.label.startsWith('Frameworks')) {
                return frameworks.map((fw: string) => new ArchitectureTreeItem(`🏛️ ${fw}`, vscode.TreeItemCollapsibleState.None, 'Framework'));
            }

            if (element.label.startsWith('Languages')) {
                return languages.map((lang: string) => {
                    const count = localData.languages[lang];
                    return new ArchitectureTreeItem(`📄 ${lang}`, vscode.TreeItemCollapsibleState.None, `${count} files`);
                });
            }

            if (element.label.startsWith('Indexed Files')) {
                const candidates = [
                    path.join(this.rootPath || '', '.wia', 'index.json'),
                    path.join(this.rootPath || '', 'Workspace-Intelligence-Agent', '.wia', 'index.json')
                ];
                for (const cand of candidates) {
                    if (fs.existsSync(cand)) {
                        try {
                            const idx = JSON.parse(fs.readFileSync(cand, 'utf8'));
                            const files = Object.keys(idx.files || {}).slice(0, 40);
                            return files.map(f => {
                                const fullPath = this.rootPath ? path.join(this.rootPath, f) : f;
                                return new ArchitectureTreeItem(f, vscode.TreeItemCollapsibleState.None, idx.files[f]?.language, undefined, fullPath);
                            });
                        } catch (e) {}
                    }
                }
            }

            return [];
        }

        return [new ArchitectureTreeItem('Run "WIA: Scan Workspace" to index codebase', vscode.TreeItemCollapsibleState.None)];
    }
}
