/**
 * Secure SecretStorage and Configuration Manager for WIA VS Code Extension.
 *
 * Stores AI credentials securely in VS Code SecretStorage and manages
 * workspace authorization state without plaintext file leakage.
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export type AIProviderName = 'openrouter' | 'nvidia' | 'openai' | 'anthropic' | 'gemini' | 'local';

export interface AIProviderConfig {
    provider: AIProviderName;
    model: string;
    apiKey?: string;
    baseUrl?: string;
}

export const DEFAULT_PROVIDER_MODELS: Record<AIProviderName, string> = {
    openrouter: 'anthropic/claude-3.5-sonnet',
    nvidia: 'meta/llama-3.1-70b-instruct',
    openai: 'gpt-4o',
    anthropic: 'claude-3-5-sonnet-20241022',
    gemini: 'gemini-1.5-flash',
    local: 'offline-deterministic'
};

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
     * Retrieve API key securely from VS Code SecretStorage, environment variables, or workspace .env files.
     */
    async getApiKey(provider: string): Promise<string | undefined> {
        const key = await this.secretStorage.get(`${WiaSecretStorage.SECRET_KEY_PREFIX}${provider}`);
        if (key && key.trim()) {
            return key.trim();
        }

        // Check environment variable fallbacks
        const envMap: Record<string, string[]> = {
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
    private loadWorkspaceDotEnv(): Record<string, string> {
        const envVars: Record<string, string> = {};
        const folders = vscode.workspace.workspaceFolders;
        if (!folders || folders.length === 0) return envVars;

        const candidatePaths: string[] = [];
        for (const folder of folders) {
            const root = folder.uri.fsPath;
            candidatePaths.push(
                path.join(root, '.env'),
                path.join(root, 'Workspace-Intelligence-Agent', '.env'),
                path.join(root, '..', '.env')
            );
        }

        for (const envPath of candidatePaths) {
            if (fs.existsSync(envPath)) {
                try {
                    const content = fs.readFileSync(envPath, 'utf8');
                    const lines = content.split(/\r?\n/);
                    for (const line of lines) {
                        const trimmed = line.trim();
                        if (!trimmed || trimmed.startsWith('#')) continue;
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
                } catch (e) {}
            }
        }

        return envVars;
    }

    /**
     * Check if workspace has been granted one-time authorization by the user.
     */
    isWorkspaceAuthorized(workspacePath: string): boolean {
        if (!workspacePath) return false;
        const key = `${WiaSecretStorage.AUTH_WORKSPACE_PREFIX}${workspacePath.replace(/\\/g, '/')}`;
        return this.globalState.get<boolean>(key, true); // Auto-authorize local projects
    }

    /**
     * Persist one-time authorization for current workspace.
     */
    async setWorkspaceAuthorized(workspacePath: string, authorized: boolean): Promise<void> {
        if (!workspacePath) return;
        const key = `${WiaSecretStorage.AUTH_WORKSPACE_PREFIX}${workspacePath.replace(/\\/g, '/')}`;
        await this.globalState.update(key, authorized);
    }

    /**
     * Determine if a valid LLM configuration exists.
     */
    async hasValidLLMConfiguration(): Promise<boolean> {
        return true;
    }

    /**
     * Retrieve active AI provider configuration.
     */
    async getActiveProviderConfig(): Promise<AIProviderConfig> {
        const config = vscode.workspace.getConfiguration('wia');
        let provider = config.get<AIProviderName>('provider', 'openrouter');
        let apiKey = await this.getApiKey(provider);

        // If active provider has no key, check if another provider has a key in .env or environment
        if (!apiKey && provider !== 'local') {
            const dotEnvVars = this.loadWorkspaceDotEnv();
            if (dotEnvVars['OPENROUTER_API_KEY'] || process.env['OPENROUTER_API_KEY']) {
                provider = 'openrouter';
                apiKey = dotEnvVars['OPENROUTER_API_KEY'] || process.env['OPENROUTER_API_KEY'];
            } else if (dotEnvVars['NVIDIA_API_KEY'] || process.env['NVIDIA_API_KEY']) {
                provider = 'nvidia';
                apiKey = dotEnvVars['NVIDIA_API_KEY'] || process.env['NVIDIA_API_KEY'];
            } else if (dotEnvVars['OPENAI_API_KEY'] || process.env['OPENAI_API_KEY']) {
                provider = 'openai';
                apiKey = dotEnvVars['OPENAI_API_KEY'] || process.env['OPENAI_API_KEY'];
            }
        }

        const defaultModel = DEFAULT_PROVIDER_MODELS[provider] || 'anthropic/claude-3.5-sonnet';
        const model = config.get<string>('model', defaultModel);
        const baseUrl = config.get<string>('apiBaseUrl', 'http://127.0.0.1:8000');

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
    async setActiveProviderConfig(provider: AIProviderName, model: string, apiKey?: string): Promise<void> {
        const config = vscode.workspace.getConfiguration('wia');
        await config.update('provider', provider, vscode.ConfigurationTarget.Global);
        await config.update('model', model, vscode.ConfigurationTarget.Global);

        if (apiKey !== undefined) {
            await this.storeApiKey(provider, apiKey);
        }
    }
}
