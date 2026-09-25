/**
 * Secure SecretStorage and Configuration Manager for WIA VS Code Extension.
 *
 * Stores AI credentials securely in VS Code SecretStorage and manages
 * workspace authorization state without plaintext file leakage.
 */

import * as vscode from 'vscode';

export interface AIProviderConfig {
    provider: 'nvidia' | 'openai' | 'anthropic' | 'gemini' | 'local';
    model: string;
    apiKey?: string;
    baseUrl?: string;
}

export class WiaSecretStorage {
    private static readonly SECRET_KEY_PREFIX = 'wia.apikey.';
    private static readonly AUTH_WORKSPACE_PREFIX = 'wia.authorized.';

    constructor(private readonly secretStorage: vscode.SecretStorage, private readonly globalState: vscode.Memento) {}

    /**
     * Store API key securely in VS Code SecretStorage.
     */
    async storeApiKey(provider: string, apiKey: string): Promise<void> {
        if (!apiKey) {
            await this.secretStorage.delete(`${WiaSecretStorage.SECRET_KEY_PREFIX}${provider}`);
            return;
        }
        await this.secretStorage.store(`${WiaSecretStorage.SECRET_KEY_PREFIX}${provider}`, apiKey.trim());
    }

    /**
     * Retrieve API key securely from VS Code SecretStorage.
     */
    async getApiKey(provider: string): Promise<string | undefined> {
        return await this.secretStorage.get(`${WiaSecretStorage.SECRET_KEY_PREFIX}${provider}`);
    }

    /**
     * Check if workspace has been granted one-time authorization by the user.
     */
    isWorkspaceAuthorized(workspacePath: string): boolean {
        const key = `${WiaSecretStorage.AUTH_WORKSPACE_PREFIX}${workspacePath.replace(/\\/g, '/')}`;
        return this.globalState.get<boolean>(key, false);
    }

    /**
     * Persist one-time authorization for current workspace.
     */
    async setWorkspaceAuthorized(workspacePath: string, authorized: boolean): Promise<void> {
        const key = `${WiaSecretStorage.AUTH_WORKSPACE_PREFIX}${workspacePath.replace(/\\/g, '/')}`;
        await this.globalState.update(key, authorized);
    }

    /**
     * Retrieve active AI provider configuration.
     */
    async getActiveProviderConfig(): Promise<AIProviderConfig> {
        const config = vscode.workspace.getConfiguration('wia');
        const provider = config.get<'nvidia' | 'openai' | 'anthropic' | 'gemini' | 'local'>('provider', 'nvidia');
        const model = config.get<string>('model', 'meta/llama-3.1-70b-instruct');
        const baseUrl = config.get<string>('apiBaseUrl', 'http://127.0.0.1:8000');
        const apiKey = await this.getApiKey(provider);

        return {
            provider,
            model,
            apiKey,
            baseUrl
        };
    }

    /**
     * Update active AI provider configuration settings.
     */
    async setActiveProviderConfig(provider: string, model: string, apiKey?: string): Promise<void> {
        const config = vscode.workspace.getConfiguration('wia');
        await config.update('provider', provider, vscode.ConfigurationTarget.Global);
        await config.update('model', model, vscode.ConfigurationTarget.Global);

        if (apiKey !== undefined) {
            await this.storeApiKey(provider, apiKey);
        }
    }
}
