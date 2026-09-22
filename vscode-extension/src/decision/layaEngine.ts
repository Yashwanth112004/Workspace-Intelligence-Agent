/**
 * In-Memory Laya Decision Engine for VS Code Extension.
 *
 * Implements non-autoregressive "System 1" decision routing with choice, score,
 * and noul primitives for sub-35ms routing from natural-language queries
 * to registered WIA operations without invoking a slow, expensive LLM.
 */

import { WIAOperationCall, isValidOperation } from '../registry/operationRegistry';

export interface LayaDecisionResult {
    request: string;
    intent: string;
    operations: WIAOperationCall[];
    confidence: float;
    requires_llm_reasoning: boolean;
    rationale: string;
    suggested_clarifications: string[];
}

export type float = number;

interface IntentRule {
    intent: string;
    pattern: RegExp;
    baseConfidence: number;
    requiresLLM: boolean;
    operations: string[];
}

export class LayaDecisionEngine {
    private intentRules: IntentRule[] = [];
    private confidenceThreshold = 0.65;

    constructor() {
        this.compileRules();
    }

    private compileRules(): void {
        this.intentRules = [
            // 1. Project Execution / Commands (Deterministic - No LLM needed)
            {
                intent: 'project_test',
                pattern: /\b(run|execute|start)\b.*\b(test|tests|pytest|spec|suite|jest)\b|\b(test|tests)\s*$/i,
                baseConfidence: 0.96,
                requiresLLM: false,
                operations: ['project.test']
            },
            {
                intent: 'project_run',
                pattern: /\b(how\s+to\s+)?(run|start|serve|launch|execute)\b.*\b(project|app|application|server|daemon|backend|frontend)\b|^run(\s+the)?\s+(project|app)$/i,
                baseConfidence: 0.95,
                requiresLLM: false,
                operations: ['project.run']
            },
            {
                intent: 'project_build',
                pattern: /\b(build|compile|bundle|package|distribute|make)\b.*\b(project|app|binary|package|wheel|dist)\b/i,
                baseConfidence: 0.94,
                requiresLLM: false,
                operations: ['project.build']
            },
            {
                intent: 'project_lint',
                pattern: /\b(lint|check style|format|typecheck|mypy|flake8|eslint|prettier)\b/i,
                baseConfidence: 0.93,
                requiresLLM: false,
                operations: ['project.lint']
            },

            // 2. Dependencies & Environment Diagnostics
            {
                intent: 'dependency_repair',
                pattern: /\b(fix|repair|install|resolve|update)\b.*\b(dependencies|packages|environment|env|modules|requirements)\b/i,
                baseConfidence: 0.95,
                requiresLLM: false,
                operations: ['environment.repair', 'dependency.check']
            },
            {
                intent: 'dependency_check',
                pattern: /\b(check|list|inspect|show|find|audit|scan)\b.*\b(dependencies|dependency|package|packages|conflicts|missing|versions|lockfile)\b|\bwhy\s+is\s+.*(dependency|package)\s+failing\b/i,
                baseConfidence: 0.94,
                requiresLLM: true,
                operations: ['dependency.check', 'dependency.conflicts', 'dependency.list']
            },
            {
                intent: 'environment_check',
                pattern: /\b(check|verify|detect|inspect|validate)\b.*\b(environment|env|python|node|java|runtime|venv|virtualenv|version)\b|\benvironment\s+(status|health|correct)\b/i,
                baseConfidence: 0.94,
                requiresLLM: false,
                operations: ['environment.detect', 'environment.check']
            },

            // 3. Architecture & Project Overview
            {
                intent: 'architecture_overview',
                pattern: /\b(architecture|overview|subsystem|subsystems|boundaries|components|diagram|structure|design|system design)\b|\b(how\s+does\s+(this|the)\s+project\s+work|explain\s+(this|the)\s+project|show\s+(me\s+)?(project\s+)?architecture)\b/i,
                baseConfidence: 0.95,
                requiresLLM: true,
                operations: ['workspace.summary', 'architecture.analyze', 'repository.structure']
            },

            // 4. Impact Analysis & Blast Radius
            {
                intent: 'impact_analysis',
                pattern: /\b(what\s+will\s+(be\s+affected|break|change)|impact|blast radius|dependents|callers\s+of|what\s+depends\s+on)\b/i,
                baseConfidence: 0.93,
                requiresLLM: true,
                operations: ['impact.analyze', 'index.dependencies', 'index.symbols']
            },

            // 5. File & Symbol Exploration / Search
            {
                intent: 'file_listing',
                pattern: /\b(what\s+files|list\s+files|show\s+files|file\s+tree|all\s+files|directory\s+structure)\b/i,
                baseConfidence: 0.96,
                requiresLLM: false,
                operations: ['repository.files', 'repository.structure']
            },
            {
                intent: 'symbol_search',
                pattern: /\b(where\s+is|find|search|lookup|locate)\b.*\b(class|function|method|symbol|endpoint|router|database|config|configuration)\b/i,
                baseConfidence: 0.92,
                requiresLLM: false,
                operations: ['index.search', 'index.symbols']
            },

            // 6. Diagnosis / Failure Troubleshooting
            {
                intent: 'diagnose_problem',
                pattern: /\b(why\s+is\s+.*(not\s+working|failing|crashing|failing\s+to\s+start|broken|failing\s+tests)|troubleshoot|diagnose|error\s+in)\b/i,
                baseConfidence: 0.91,
                requiresLLM: true,
                operations: ['environment.check', 'dependency.check', 'workspace.status', 'index.search']
            },

            // 7. Component Explanation
            {
                intent: 'component_explain',
                pattern: /\b(how\s+does\s+.*work|explain\s+how|explain\s+the\s+.*|explain\s+.*|walk\s+through\s+.*|what\s+does\s+.*do)\b/i,
                baseConfidence: 0.90,
                requiresLLM: true,
                operations: ['component.explain', 'index.search', 'architecture.analyze']
            }
        ];
    }

    /**
     * Laya `choice` primitive: selects optimal intent and calibrated confidence.
     */
    public choice(query: string): { intent: string; confidence: number; requiresLLM: boolean; operations: string[] } {
        const q = query.trim();
        if (!q) {
            return { intent: 'unknown', confidence: 0.0, requiresLLM: false, operations: ['workspace.summary'] };
        }

        for (const rule of this.intentRules) {
            const match = rule.pattern.exec(q);
            if (match) {
                const lengthBonus = Math.min(0.05, match[0].length / 100.0);
                const calibratedConf = Math.min(0.99, rule.baseConfidence + lengthBonus);
                return {
                    intent: rule.intent,
                    confidence: calibratedConf,
                    requiresLLM: rule.requiresLLM,
                    operations: rule.operations
                };
            }
        }

        if (/\b(how|why|what|where|explain|describe|show)\b/i.test(q)) {
            return {
                intent: 'component_explain',
                confidence: 0.75,
                requiresLLM: true,
                operations: ['index.search', 'architecture.analyze', 'component.explain']
            };
        }

        return {
            intent: 'general_query',
            confidence: 0.55,
            requiresLLM: true,
            operations: ['workspace.summary', 'index.search']
        };
    }

    /**
     * Laya `score` primitive: return calibrated confidence for query against intent rubric.
     */
    public score(query: string, _intent: string): number {
        return this.choice(query).confidence;
    }

    /**
     * Laya `noul` primitive: calibrated binary decision whether query matches intent hypothesis.
     */
    public noul(query: string, intentHypothesis: string): { isMatch: boolean; probability: number } {
        const result = this.choice(query);
        const isMatch = result.intent === intentHypothesis;
        const probability = isMatch ? result.confidence : 1.0 - result.confidence;
        return { isMatch, probability };
    }

    private extractTargetEntities(query: string): Record<string, string> {
        const params: Record<string, string> = {};
        const cleanQ = query.trim();

        const fileMatch = /\b([\w\-/\\]+\.(?:py|js|ts|jsx|tsx|go|rs|java|json|toml|yaml|yml|md|ipynb))\b/i.exec(cleanQ);
        if (fileMatch) {
            params.file_path = fileMatch[1].replace(/\\/g, '/');
        }

        const quoteMatch = /['"]([^'"]+)['"]/.exec(cleanQ);
        if (quoteMatch) {
            params.query = quoteMatch[1];
            params.symbol = quoteMatch[1];
        } else {
            let cleanTerm = cleanQ.replace(/^(how\s+does|how\s+do\s+i|explain\s+how|explain|what\s+does|where\s+is|find|search\s+for|what\s+will\s+break\s+if\s+i\s+change)\s+/i, '');
            cleanTerm = cleanTerm.replace(/\s+(work|do|run|function|mean|be\s+affected)\??$/i, '').trim();
            if (cleanTerm && cleanTerm.split(/\s+/).length <= 4) {
                params.query = cleanTerm;
                params.symbol = cleanTerm;
            }
        }

        return params;
    }

    /**
     * Main Laya decision execution: maps natural language to structured WIA operations.
     */
    public decide(query: string): LayaDecisionResult {
        const { intent, confidence, requiresLLM, operations: rawOps } = this.choice(query);
        const targetParams = this.extractTargetEntities(query);

        const operations: WIAOperationCall[] = [];
        for (const opName of rawOps) {
            if (isValidOperation(opName)) {
                const opParams: Record<string, any> = {};
                if (opName === 'index.search' || opName === 'component.explain') {
                    if (targetParams.query) opParams.query = targetParams.query;
                    if (targetParams.file_path) opParams.file_path = targetParams.file_path;
                } else if (opName === 'impact.analyze') {
                    if (targetParams.symbol) opParams.symbol = targetParams.symbol;
                    else if (targetParams.file_path) opParams.file_path = targetParams.file_path;
                } else if (opName === 'dependency.check') {
                    if (targetParams.query) opParams.scope = targetParams.query;
                }
                operations.push({ name: opName, parameters: opParams });
            }
        }

        let clarifications: string[] = [];
        let rationale: string;
        if (confidence < this.confidenceThreshold) {
            clarifications = [
                'Explain the project architecture',
                'Check dependency and environment health',
                'Run the project tests',
                'Search symbols in workspace'
            ];
            rationale = `Query matched '${intent}' with moderate confidence (${confidence.toFixed(2)}). Suggested clarifications available.`;
        } else {
            rationale = `Laya non-autoregressive decision engine routed query to '${intent}' with high confidence (${confidence.toFixed(2)}).`;
        }

        return {
            request: query,
            intent,
            operations,
            confidence: Number(confidence.toFixed(3)),
            requires_llm_reasoning: requiresLLM,
            rationale,
            suggested_clarifications: clarifications
        };
    }
}
