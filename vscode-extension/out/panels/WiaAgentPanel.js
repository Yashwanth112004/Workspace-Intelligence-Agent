"use strict";
/**
 * WiaAgentPanel: Helper delegator to focus the canonical WIA Agent View.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaAgentPanel = void 0;
const vscode = require("vscode");
class WiaAgentPanel {
    static currentPanel;
    static async createOrShow(_extensionUri, _apiClient, _secretStorage, _layaEngine, _executor, _envRepair, _workspaceRoot, _repoId) {
        await vscode.commands.executeCommand('workbench.view.extension.wia-container');
        await vscode.commands.executeCommand('wia-agent-view.focus');
    }
}
exports.WiaAgentPanel = WiaAgentPanel;
//# sourceMappingURL=WiaAgentPanel.js.map