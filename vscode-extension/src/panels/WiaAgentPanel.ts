/**
 * WiaAgentPanel: Helper delegator to focus the canonical WIA Agent View.
 */

import * as vscode from 'vscode';
import { WiaApiClient } from '../apiClient';
import { WiaSecretStorage } from '../auth/secretStorage';
import { LayaDecisionEngine } from '../decision/layaEngine';
import { WiaExecutor } from '../executor/wiaExecutor';
import { EnvironmentRepairEngine } from '../environment/envRepair';

export class WiaAgentPanel {
    public static currentPanel: WiaAgentPanel | undefined;

    public static async createOrShow(
        _extensionUri: vscode.Uri,
        _apiClient: WiaApiClient,
        _secretStorage: WiaSecretStorage,
        _layaEngine: LayaDecisionEngine,
        _executor: WiaExecutor,
        _envRepair: EnvironmentRepairEngine,
        _workspaceRoot: string | null,
        _repoId: string | null
    ) {
        await vscode.commands.executeCommand('workbench.view.extension.wia-container');
        await vscode.commands.executeCommand('wia-agent-view.focus');
    }
}
