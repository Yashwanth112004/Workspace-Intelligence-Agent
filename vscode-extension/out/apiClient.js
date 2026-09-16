"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WiaApiClient = void 0;
const http = require("http");
class WiaApiClient {
    baseUrl;
    constructor(baseUrl = 'http://127.0.0.1:8000') {
        this.baseUrl = baseUrl;
    }
    request(method, path, body) {
        return new Promise((resolve, reject) => {
            const url = new URL(this.baseUrl + path);
            const req = http.request({
                hostname: url.hostname,
                port: url.port,
                path: url.pathname + url.search,
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            }, (res) => {
                let data = '';
                res.on('data', (chunk) => (data += chunk));
                res.on('end', () => {
                    try {
                        const parsed = JSON.parse(data);
                        resolve(parsed);
                    }
                    catch (e) {
                        resolve(data);
                    }
                });
            });
            req.on('error', (err) => reject(err));
            if (body) {
                req.write(JSON.stringify(body));
            }
            req.end();
        });
    }
    async ingest(sourcePath, name) {
        return this.request('POST', '/api/v1/ingest', { source_path: sourcePath, name });
    }
    async getStatus(repoId) {
        return this.request('GET', `/api/v1/repos/${repoId}/status`);
    }
    async getTree(repoId) {
        return this.request('GET', `/api/v1/repos/${repoId}/tree`);
    }
    async getArchitecture(repoId) {
        return this.request('GET', `/api/v1/repos/${repoId}/architecture`);
    }
    async searchSymbols(repoId, query = '') {
        return this.request('GET', `/api/v1/repos/${repoId}/symbols/search?q=${encodeURIComponent(query || 'a')}`);
    }
    async getDependencies(repoId) {
        return this.request('GET', `/api/v1/repos/${repoId}/dependencies/graph`);
    }
    async query(repoId, queryText) {
        return this.request('POST', `/api/v1/repos/${repoId}/query`, { query: queryText });
    }
    async traceFlow(repoId, entrySymbol) {
        return this.request('GET', `/api/v1/repos/${repoId}/flow?entry=${encodeURIComponent(entrySymbol)}`);
    }
    async analyzeImpact(repoId, target) {
        return this.request('GET', `/api/v1/repos/${repoId}/impact?target=${encodeURIComponent(target)}`);
    }
    async exportOkf(repoId) {
        return this.request('GET', `/api/v1/repos/${repoId}/export?format=okf`);
    }
}
exports.WiaApiClient = WiaApiClient;
//# sourceMappingURL=apiClient.js.map