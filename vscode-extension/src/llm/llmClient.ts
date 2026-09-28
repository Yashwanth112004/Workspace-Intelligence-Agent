/**
 * LLM Provider Client for WIA AI Fallback Reasoning Layer.
 *
 * Supports OpenRouter, NVIDIA NIM, OpenAI, Anthropic, Google Gemini, and Local.
 */

import { AIProviderConfig } from '../auth/secretStorage';

export class WiaLLMClient {
    /**
     * Send grounded reasoning prompt to configured LLM provider.
     */
    public async answerWithContext(
        userQuery: string,
        groundedContext: string,
        config: AIProviderConfig
    ): Promise<string> {
        if (config.provider === 'local') {
            return `### Offline Local Analysis\n\nBased on your indexed workspace context:\n\n${groundedContext}\n\n*Note: Configure an AI API key (OpenRouter, NVIDIA, OpenAI, etc.) in WIA settings for deeper semantic synthesis.*`;
        }

        if (!config.apiKey) {
            throw new Error(`No API key configured for provider '${config.provider}'. Please configure your key in WIA settings.`);
        }

        const systemPrompt = `You are WIA (Workspace Intelligence Agent), an expert AI software architect and developer pair programmer.
Answer the developer's question directly, concisely, and accurately based on the provided grounded codebase context.
Use clean markdown with code snippets where helpful. Do not mention internal routing.`;

        const userContent = `Here is the relevant grounded context from the workspace:\n\n${groundedContext}\n\nUser Question: ${userQuery}`;

        switch (config.provider) {
            case 'openrouter':
            case 'nvidia':
            case 'openai':
                return this.callOpenAICompatible(config, systemPrompt, userContent);
            case 'anthropic':
                return this.callAnthropic(config, systemPrompt, userContent);
            case 'gemini':
                return this.callGemini(config, systemPrompt, userContent);
            default:
                return this.callOpenAICompatible(config, systemPrompt, userContent);
        }
    }

    /**
     * Perform a live test probe against the configured AI provider.
     */
    public async testProviderConnection(config: AIProviderConfig): Promise<{ success: boolean; message: string }> {
        if (config.provider === 'local') {
            return { success: true, message: 'Offline deterministic engine is active and ready.' };
        }
        if (!config.apiKey || !config.apiKey.trim()) {
            return { success: false, message: `No API key provided for ${config.provider.toUpperCase()}.` };
        }

        const key = config.apiKey.trim();
        try {
            if (config.provider === 'openrouter') {
                const res = await fetch('https://openrouter.ai/api/v1/auth/key', {
                    headers: {
                        'Authorization': `Bearer ${key}`,
                        'HTTP-Referer': 'https://github.com/wia/workspace-intelligence-agent',
                        'X-Title': 'WIA VS Code Extension'
                    }
                });
                if (res.status === 200) {
                    const data: any = await res.json();
                    const label = data.data?.label || 'Verified Key';
                    const usage = typeof data.data?.usage === 'number' ? ` (Usage: $${data.data.usage.toFixed(2)})` : '';
                    return { success: true, message: `Connected to OpenRouter (${label})${usage}.` };
                } else if (res.status === 401) {
                    return { success: false, message: 'OpenRouter authentication failed (HTTP 401): Invalid API key.' };
                } else {
                    const txt = await res.text();
                    return { success: false, message: `OpenRouter returned HTTP ${res.status}: ${txt.slice(0, 100)}` };
                }
            } else if (config.provider === 'nvidia') {
                const res = await fetch('https://integrate.api.nvidia.com/v1/models', {
                    headers: { 'Authorization': `Bearer ${key}` }
                });
                if (res.status === 200) {
                    return { success: true, message: 'Successfully verified NVIDIA NIM API credentials.' };
                } else if (res.status === 401) {
                    return { success: false, message: 'NVIDIA NIM authentication failed (HTTP 401): Invalid API key.' };
                } else {
                    return { success: false, message: `NVIDIA NIM returned HTTP ${res.status}.` };
                }
            } else if (config.provider === 'openai') {
                const res = await fetch('https://api.openai.com/v1/models', {
                    headers: { 'Authorization': `Bearer ${key}` }
                });
                if (res.status === 200) {
                    return { success: true, message: 'Successfully verified OpenAI API credentials.' };
                } else if (res.status === 401) {
                    return { success: false, message: 'OpenAI authentication failed (HTTP 401): Invalid API key.' };
                } else {
                    return { success: false, message: `OpenAI returned HTTP ${res.status}.` };
                }
            }
            return { success: true, message: `Configured credentials for ${config.provider.toUpperCase()}.` };
        } catch (err: any) {
            const detail = err.cause ? (err.cause.message || err.cause.code || String(err.cause)) : err.message;
            return { success: false, message: `Connection error reaching ${config.provider}: ${detail || err.message}` };
        }
    }

    private async callOpenAICompatible(
        config: AIProviderConfig,
        systemPrompt: string,
        userContent: string
    ): Promise<string> {
        let endpoint = 'https://openrouter.ai/api/v1/chat/completions';
        if (config.provider === 'nvidia') {
            endpoint = 'https://integrate.api.nvidia.com/v1/chat/completions';
        } else if (config.provider === 'openai') {
            endpoint = 'https://api.openai.com/v1/chat/completions';
        }

        let response: Response;
        try {
            response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${config.apiKey!.trim()}`,
                    'HTTP-Referer': 'https://github.com/wia/workspace-intelligence-agent',
                    'X-Title': 'WIA VS Code Extension'
                },
                body: JSON.stringify({
                    model: config.model.trim(),
                    messages: [
                        { role: 'system', content: systemPrompt },
                        { role: 'user', content: userContent }
                    ],
                    temperature: 0.2,
                    max_tokens: 2048
                })
            });
        } catch (fetchErr: any) {
            const detail = fetchErr.cause ? (fetchErr.cause.message || fetchErr.cause.code || String(fetchErr.cause)) : fetchErr.message;
            throw new Error(`Failed to reach ${config.provider} (${endpoint}): ${detail || fetchErr.message}`);
        }

        if (!response.ok) {
            const errText = await response.text();
            let parsedMsg = errText;
            try {
                const j = JSON.parse(errText);
                parsedMsg = j.error?.message || j.message || errText;
            } catch (e) {}

            if (response.status === 401) {
                throw new Error(`${config.provider.toUpperCase()} Authentication Failed (HTTP 401): Invalid API key.`);
            } else if (response.status === 404) {
                throw new Error(`${config.provider.toUpperCase()} Model Not Found (HTTP 404): '${config.model}' is not available on this provider.`);
            } else if (response.status === 429) {
                throw new Error(`${config.provider.toUpperCase()} Rate Limit Exceeded (HTTP 429): ${parsedMsg}`);
            } else {
                throw new Error(`${config.provider.toUpperCase()} API Error (HTTP ${response.status}): ${parsedMsg}`);
            }
        }

        const data: any = await response.json();
        return data.choices?.[0]?.message?.content || 'No response generated from provider.';
    }

    private async callAnthropic(
        config: AIProviderConfig,
        systemPrompt: string,
        userContent: string
    ): Promise<string> {
        const endpoint = 'https://api.anthropic.com/v1/messages';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': config.apiKey!,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: config.model,
                system: systemPrompt,
                messages: [{ role: 'user', content: userContent }],
                max_tokens: 2048
            })
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Anthropic API returned error (${response.status}): ${errText}`);
        }

        const data: any = await response.json();
        return data.content?.[0]?.text || 'No response generated from Anthropic.';
    }

    private async callGemini(
        config: AIProviderConfig,
        systemPrompt: string,
        userContent: string
    ): Promise<string> {
        const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent?key=${config.apiKey}`;
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                system_instruction: { parts: [{ text: systemPrompt }] },
                contents: [{ parts: [{ text: userContent }] }],
                generationConfig: { temperature: 0.2, maxOutputTokens: 2048 }
            })
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Gemini API returned error (${response.status}): ${errText}`);
        }

        const data: any = await response.json();
        return data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response generated from Gemini.';
    }
}
