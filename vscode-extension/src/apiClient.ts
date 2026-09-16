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
}

export class WiaApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = 'http://127.0.0.1:8000') {
        this.baseUrl = baseUrl;
    }

    private request<T>(method: string, path: string, body?: any): Promise<T> {
        return new Promise((resolve, reject) => {
            const url = new URL(this.baseUrl + path);
            const req = http.request(
                {
                    hostname: url.hostname,
                    port: url.port,
                    path: url.pathname + url.search,
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                },
                (res) => {
                    let data = '';
                    res.on('data', (chunk) => (data += chunk));
                    res.on('end', () => {
                        try {
                            const parsed = JSON.parse(data);
                            resolve(parsed);
                        } catch (e) {
                            resolve(data as any);
                        }
                    });
                }
            );

            req.on('error', (err) => reject(err));
            if (body) {
                req.write(JSON.stringify(body));
            }
            req.end();
        });
    }

    async ingest(sourcePath: string, name?: string): Promise<IngestResponse> {
        return this.request<IngestResponse>('POST', '/api/v1/ingest', { source_path: sourcePath, name });
    }

    async getStatus(repoId: string): Promise<WiaStatusResponse> {
        return this.request<WiaStatusResponse>('GET', `/api/v1/repos/${repoId}/status`);
    }

    async getTree(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${repoId}/tree`);
    }

    async getArchitecture(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${repoId}/architecture`);
    }

    async searchSymbols(repoId: string, query: string = ''): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${repoId}/symbols/search?q=${encodeURIComponent(query || 'a')}`);
    }

    async getDependencies(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${repoId}/dependencies/graph`);
    }

    async query(repoId: string, queryText: string): Promise<any> {
        return this.request<any>('POST', `/api/v1/repos/${repoId}/query`, { query: queryText });
    }

    async traceFlow(repoId: string, entrySymbol: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${repoId}/flow?entry=${encodeURIComponent(entrySymbol)}`);
    }

    async analyzeImpact(repoId: string, target: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${repoId}/impact?target=${encodeURIComponent(target)}`);
    }

    async exportOkf(repoId: string): Promise<any> {
        return this.request<any>('GET', `/api/v1/repos/${repoId}/export?format=okf`);
    }
}
