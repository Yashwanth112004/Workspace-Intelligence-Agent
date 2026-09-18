import * as http from 'http';

export interface IngestResponse {
    repo_id: string;
    name: string;
    status: string;
    message: string;
}

export interface WiaStatusResponse {
    repo_id: string;
    name: string;
    status: string;
    progress_pct: number;
    total_files: number;
    total_loc: number;
    tech_stack: Record<string, number>;
    entry_points: string[];
    dependencies?: string[];
    config_files?: string[];
    status_message?: string;
}

export interface ImpactResponse {
    repo_id: string;
    target: string;
    target_type?: string;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN' | 'NOT_FOUND';
    direct_impact_count: number;
    direct_impacts: Array<{
        name: string;
        symbol_type: string;
        file_path: string;
        line?: number;
    }>;
    affected_files_count: number;
    affected_files: string[];
    explanation?: string;
    evidence?: string[];
}

export interface ArchitectureResponse {
    repo_id: string;
    total_nodes: number;
    total_edges: number;
    nodes: Array<{
        id: string;
        name: string;
        type: string;
        file?: string;
        subsystem?: string;
    }>;
    edges: Array<{
        source: string;
        target: string;
        relation: string;
    }>;
    subsystems?: Array<{
        name: string;
        role: string;
        file_count: number;
        symbol_count: number;
    }>;
    circular_dependencies?: string[];
    entry_points?: string[];
    high_fan_in?: Array<[string, number, string]>;
    high_fan_out?: Array<[string, number, string]>;
}

export class WiaApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = 'http://127.0.0.1:8000') {
        this.baseUrl = baseUrl.replace(/\/+$/, '');
    }

    public setBaseUrl(url: string) {
        this.baseUrl = url.replace(/\/+$/, '');
    }

    public getBaseUrl(): string {
        return this.baseUrl;
    }

    private request<T>(method: string, path: string, body?: any, timeoutMs: number = 8000): Promise<T> {
        return new Promise((resolve, reject) => {
            try {
                const fullUrl = new URL(this.baseUrl + path);
                const req = http.request(
                    {
                        hostname: fullUrl.hostname,
                        port: fullUrl.port || (fullUrl.protocol === 'https:' ? 443 : 80),
                        path: fullUrl.pathname + fullUrl.search,
                        method: method,
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        timeout: timeoutMs
                    },
                    (res) => {
                        let data = '';
                        res.on('data', (chunk) => (data += chunk));
                        res.on('end', () => {
                            if (res.statusCode && res.statusCode >= 400) {
                                try {
                                    const parsed = JSON.parse(data);
                                    reject(new Error(parsed.detail || `HTTP Error ${res.statusCode}`));
                                } catch {
                                    reject(new Error(`HTTP Error ${res.statusCode}: ${data}`));
                                }
                                return;
                            }
                            try {
                                const parsed = JSON.parse(data);
                                resolve(parsed);
                            } catch {
                                resolve(data as any);
                            }
                        });
                    }
                );

                req.on('timeout', () => {
                    req.destroy();
                    reject(new Error(`Request timed out after ${timeoutMs}ms`));
                });

                req.on('error', (err) => reject(err));

                if (body) {
                    req.write(JSON.stringify(body));
                }
                req.end();
            } catch (err) {
                reject(err);
            }
        });
    }

    async checkHealth(): Promise<boolean> {
        try {
            const res = await this.request<any>('GET', '/health', undefined, 2500);
            return res && (res.status === 'healthy' || res.name !== undefined);
        } catch {
            return false;
        }
    }

    async ingest(sourcePath: string, name?: string): Promise<IngestResponse> {
        return this.request<IngestResponse>('POST', '/api/v1/ingest', { source_path: sourcePath, name });
    }

    async getStatus(repoId: string): Promise<WiaStatusResponse> {
        return this.request<WiaStatusResponse>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/status`);
    }

    async getTree(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/tree`);
    }

    async getFileDetails(repoId: string, filePath: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/file?path=${encodeURIComponent(filePath)}`);
    }

    async getArchitecture(repoId: string): Promise<ArchitectureResponse> {
        return this.request<ArchitectureResponse>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/architecture`);
    }

    async searchSymbols(repoId: string, query: string = '', symbolType?: string): Promise<any> {
        let path = `/api/v1/repos/${encodeURIComponent(repoId)}/symbols/search?q=${encodeURIComponent(query || 'a')}`;
        if (symbolType) {
            path += `&symbol_type=${encodeURIComponent(symbolType)}`;
        }
        return this.request<any>('GET', path);
    }

    async getDependencies(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/dependencies/graph`);
    }

    async query(repoId: string, queryText: string): Promise<any> {
        return this.request<any>('POST', `/api/v1/repos/${encodeURIComponent(repoId)}/query`, { query: queryText }, 30000);
    }

    async traceFlow(repoId: string, entrySymbol: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/flow?entry=${encodeURIComponent(entrySymbol)}`);
    }

    async analyzeImpact(repoId: string, target: string): Promise<ImpactResponse> {
        return this.request<ImpactResponse>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/impact?target=${encodeURIComponent(target)}`);
    }

    async exportOkf(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/export?format=okf`);
    }

    async getMetrics(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/metrics`);
    }

    async getHealthAudit(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/health`);
    }

    async getOnboardingGuide(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${encodeURIComponent(repoId)}/onboard`);
    }
}
