"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaApiClient = void 0;
const http = require("http");
class WiaApiClient {
    baseUrl;
    constructor(baseUrl = 'http://127.0.0.1:8000') {
        this.baseUrl = baseUrl.replace(/\/+$/, '');
    }
    setBaseUrl(url) {
        this.baseUrl = url.replace(/\/+$/, '');
    }
    getBaseUrl() {
        return this.baseUrl;
    }
    request(method, path, body, timeoutMs = 8000) {
        return new Promise((resolve, reject) => {
            try {
                const fullUrl = new URL(this.baseUrl + path);
                const req = http.request({
                    hostname: fullUrl.hostname,
                    port: fullUrl.port || (fullUrl.protocol === 'https:' ? 443 : 80),
                    path: fullUrl.pathname + fullUrl.search,
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    timeout: timeoutMs
                }, (res) => {
                    let data = '';
                    res.on('data', (chunk) => (data += chunk));
                    res.on('end', () => {
                        if (res.statusCode && res.statusCode >= 400) {
                            try {
                                const parsed = JSON.parse(data);
                                reject(new Error(parsed.detail || `HTTP Error ${res.statusCode}`));
                            }
                            catch {
                                reject(new Error(`HTTP Error ${res.statusCode}: ${data}`));
                            }
                            return;
                        }
                        try {
                            const parsed = JSON.parse(data);
                            resolve(parsed);
                        }
                        catch {
                            resolve(data);
                        }
                    });
                });
                req.on('timeout', () => {
                    req.destroy();
                    reject(new Error(`Request timed out after ${timeoutMs}ms`));
                });
                req.on('error', (err) => reject(err));
                if (body) {
                    req.write(JSON.stringify(body));
                }
                req.end();
            }
            catch (err) {
                reject(err);
            }
        });
    }
    async checkHealth() {
        try {
            const res = await this.request('GET', '/health', undefined, 2500);
            return res && (res.status === 'healthy' || res.name !== undefined);
        }
        catch {
            return false;
        }
    }
    async ingest(sourcePath, name) {
        return this.request('POST', '/api/v1/ingest', { source_path: sourcePath, name });
    }
    async getStatus(repoId) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/status`);
    }
    async getTree(repoId) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/tree`);
    }
    async getFileDetails(repoId, filePath) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/file?path=${encodeURIComponent(filePath)}`);
    }
    async getArchitecture(repoId) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/architecture`);
    }
    async searchSymbols(repoId, query = '', symbolType) {
        let path = `/api/v1/repos/${encodeURIComponent(repoId)}/symbols/search?q=${encodeURIComponent(query || 'a')}`;
        if (symbolType) {
            path += `&symbol_type=${encodeURIComponent(symbolType)}`;
        }
        return this.request('GET', path);
    }
    async getDependencies(repoId) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/dependencies/graph`);
    }
    async query(repoId, queryText) {
        return this.request('POST', `/api/v1/repos/${encodeURIComponent(repoId)}/query`, { query: queryText }, 30000);
    }
    async traceFlow(repoId, entrySymbol) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/flow?entry=${encodeURIComponent(entrySymbol)}`);
    }
    async analyzeImpact(repoId, target) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/impact?target=${encodeURIComponent(target)}`);
    }
    async exportOkf(repoId) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/export?format=okf`);
    }
    async getMetrics(repoId) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/metrics`);
    }
    async getHealthAudit(repoId) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/health`);
    }
    async getOnboardingGuide(repoId) {
        return this.request('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/onboard`);
    }
}
exports.WiaApiClient = WiaApiClient;
//# sourceMappingURL=apiClient.js.map