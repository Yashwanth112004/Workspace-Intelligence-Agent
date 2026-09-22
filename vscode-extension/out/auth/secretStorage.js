"use strict";
/**
 * Secure SecretStorage and Configuration Manager for WIA VS Code Extension.
 *
 * Stores AI credentials securely in VS Code SecretStorage and manages
 * workspace authorization state without plaintext file leakage.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaSecretStorage = void 0;
const vscode = require("vscode");
class WiaSecretStorage {
    secretStorage;
    globalState;
    static SECRET_KEY_PREFIX = 'wia.apikey.';
    static AUTH_WORKSPACE_PREFIX = 'wia.authorized.';
    constructor(secretStorage, globalState) {
        this.secretStorage = secretStorage;
        this.globalState = globalState;
    }
    /**
     * Store API key securely in VS Code SecretStorage.
     */
    async storeApiKey(provider, apiKey) {
        if (!apiKey) {
            await this.secretStorage.delete(`${WiaSecretStorage.SECRET_KEY_PREFIX}${provider}`);
            return;
        }
        await this.secretStorage.store(`${WiaSecretStorage.SECRET_KEY_PREFIX}${provider}`, apiKey.trim());
    }
    /**
     * Retrieve API key securely from VS Code SecretStorage.
     */
    async getApiKey(provider) {
        return await this.secretStorage.get(`${WiaSecretStorage.SECRET_KEY_PREFIX}${provider}`);
    }
    /**
     * Check if workspace has been granted one-time authorization by the user.
     */
    isWorkspaceAuthorized(workspacePath) {
        const key = `${WiaSecretStorage.AUTH_WORKSPACE_PREFIX}${workspacePath.replace(/\\/g, '/')}`;
        return this.globalState.get(key, false);
    }
    /**
     * Persist one-time authorization for current workspace.
     */
    async setWorkspaceAuthorized(workspacePath, authorized) {
        const key = `${WiaSecretStorage.AUTH_WORKSPACE_PREFIX}${workspacePath.replace(/\\/g, '/')}`;
        await this.globalState.update(key, authorized);
    }
    /**
     * Retrieve active AI provider configuration.
     */
    async getActiveProviderConfig() {
        const config = vscode.workspace.getConfiguration('wia');
        const provider = config.get('provider', 'nvidia');
        const model = config.get('model', 'meta/llama-3.1-70b-instruct');
        const baseUrl = config.get('apiBaseUrl', 'http://127.0.0.1:8000');
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
    async setActiveProviderConfig(provider, model, apiKey) {
        const config = vscode.workspace.getConfiguration('wia');
        await config.update('provider', provider, vscode.ConfigurationTarget.Global);
        await config.update('model', model, vscode.ConfigurationTarget.Global);
        if (apiKey !== undefined) {
            await this.storeApiKey(provider, apiKey);
        }
    }
}
exports.WiaSecretStorage = WiaSecretStorage;
//# sourceMappingURL=secretStorage.js.map