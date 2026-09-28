"use strict";
/**
 * Secure SecretStorage and Configuration Manager for WIA VS Code Extension.
 *
 * Stores AI credentials securely in VS Code SecretStorage and manages
 * workspace authorization state without plaintext file leakage.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaSecretStorage = exports.DEFAULT_PROVIDER_MODELS = void 0;
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
exports.DEFAULT_PROVIDER_MODELS = {
    openrouter: 'anthropic/claude-3.5-sonnet',
    nvidia: 'meta/llama-3.1-70b-instruct',
    openai: 'gpt-4o',
    anthropic: 'claude-3-5-sonnet-20241022',
    gemini: 'gemini-1.5-flash',
    local: 'offline-deterministic'
};
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
     * Retrieve API key securely from VS Code SecretStorage, environment variables, or workspace .env files.
     */
    async getApiKey(provider) {
        const key = await this.secretStorage.get(`${WiaSecretStorage.SECRET_KEY_PREFIX}${provider}`);
        if (key && key.trim()) {
            return key.trim();
        }
        // Check environment variable fallbacks
        const envMap = {
            openrouter: ['OPENROUTER_API_KEY'],
            nvidia: ['NVIDIA_API_KEY', 'NVIDIA_NIM_API_KEY', 'NIM_API_KEY'],
            openai: ['OPENAI_API_KEY', 'GROQ_API_KEY'],
            anthropic: ['ANTHROPIC_API_KEY'],
            gemini: ['GEMINI_API_KEY', 'GOOGLE_API_KEY']
        };
        const envVars = envMap[provider] || [];
        for (const envVar of envVars) {
            if (process.env[envVar]) {
                return process.env[envVar];
            }
        }
        // Check workspace .env files
        const dotEnvVars = this.loadWorkspaceDotEnv();
        for (const envVar of envVars) {
            if (dotEnvVars[envVar]) {
                return dotEnvVars[envVar];
            }
        }
        return undefined;
    }
    /**
     * Parse key-value pairs from .env files in workspace folders and common subdirectories.
     */
    loadWorkspaceDotEnv() {
        const envVars = {};
        const folders = vscode.workspace.workspaceFolders;
        if (!folders || folders.length === 0)
            return envVars;
        const candidatePaths = [];
        for (const folder of folders) {
            const root = folder.uri.fsPath;
            candidatePaths.push(path.join(root, '.env'), path.join(root, 'Workspace-Intelligence-Agent', '.env'), path.join(root, '..', '.env'));
        }
        for (const envPath of candidatePaths) {
            if (fs.existsSync(envPath)) {
                try {
                    const content = fs.readFileSync(envPath, 'utf8');
                    const lines = content.split(/\r?\n/);
                    for (const line of lines) {
                        const trimmed = line.trim();
                        if (!trimmed || trimmed.startsWith('#'))
                            continue;
                        const eqIdx = trimmed.indexOf('=');
                        if (eqIdx > 0) {
                            const k = trimmed.slice(0, eqIdx).trim();
                            let v = trimmed.slice(eqIdx + 1).trim();
                            if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
                                v = v.slice(1, -1);
                            }
                            if (k && v && !envVars[k]) {
                                envVars[k] = v;
                            }
                        }
                    }
                }
                catch (e) { }
            }
        }
        return envVars;
    }
    /**
     * Check if workspace has been granted one-time authorization by the user.
     */
    isWorkspaceAuthorized(workspacePath) {
        if (!workspacePath)
            return false;
        const key = `${WiaSecretStorage.AUTH_WORKSPACE_PREFIX}${workspacePath.replace(/\\/g, '/')}`;
        return this.globalState.get(key, true); // Auto-authorize local projects
    }
    /**
     * Persist one-time authorization for current workspace.
     */
    async setWorkspaceAuthorized(workspacePath, authorized) {
        if (!workspacePath)
            return;
        const key = `${WiaSecretStorage.AUTH_WORKSPACE_PREFIX}${workspacePath.replace(/\\/g, '/')}`;
        await this.globalState.update(key, authorized);
    }
    /**
     * Determine if a valid LLM configuration exists.
     */
    async hasValidLLMConfiguration() {
        const cfg = await this.getActiveProviderConfig();
        if (cfg.provider === 'local') {
            return true;
        }
        if (cfg.apiKey && cfg.apiKey.trim().length > 0) {
            return true;
        }
        // If no key for current provider, check if another provider has a key available
        const dotEnvVars = this.loadWorkspaceDotEnv();
        if (dotEnvVars['OPENROUTER_API_KEY'] || dotEnvVars['NVIDIA_API_KEY'] || dotEnvVars['OPENAI_API_KEY'] || dotEnvVars['ANTHROPIC_API_KEY'] || dotEnvVars['GEMINI_API_KEY']) {
            return true;
        }
        return false;
    }
    /**
     * Retrieve active AI provider configuration.
     */
    async getActiveProviderConfig() {
        const config = vscode.workspace.getConfiguration('wia');
        let provider = config.get('provider', 'openrouter');
        let apiKey = await this.getApiKey(provider);
        // If active provider has no key, check if another provider has a key in .env or environment
        if (!apiKey && provider !== 'local') {
            const dotEnvVars = this.loadWorkspaceDotEnv();
            if (dotEnvVars['OPENROUTER_API_KEY'] || process.env['OPENROUTER_API_KEY']) {
                provider = 'openrouter';
                apiKey = dotEnvVars['OPENROUTER_API_KEY'] || process.env['OPENROUTER_API_KEY'];
            }
            else if (dotEnvVars['NVIDIA_API_KEY'] || process.env['NVIDIA_API_KEY']) {
                provider = 'nvidia';
                apiKey = dotEnvVars['NVIDIA_API_KEY'] || process.env['NVIDIA_API_KEY'];
            }
            else if (dotEnvVars['OPENAI_API_KEY'] || process.env['OPENAI_API_KEY']) {
                provider = 'openai';
                apiKey = dotEnvVars['OPENAI_API_KEY'] || process.env['OPENAI_API_KEY'];
            }
        }
        const defaultModel = exports.DEFAULT_PROVIDER_MODELS[provider] || 'anthropic/claude-3.5-sonnet';
        const model = config.get('model', defaultModel);
        const baseUrl = config.get('apiBaseUrl', 'http://127.0.0.1:8000');
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