"use strict";
/**
 * Laya Non-Autoregressive Decision Engine and Router with JEV Similarity.
 *
 * Implements the core WIA routing specification:
 * 1. User query enters Laya.
 * 2. Laya evaluates against canonical WIA Command Registry, JEV (Jaccard-Edit-Vector) similarity, and editor context.
 * 3. Returns either:
 *    - route_type: 'wia_command' -> exact WIA CLI command to execute
 *    - route_type: 'ai_fallback'  -> LLM reasoning layer with grounded workspace context
 *
 * Zero generic collapse to architecture. Zero duplicate UI routing.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.LayaDecisionEngine = exports.JEVRouter = exports.COMMAND_DOMAIN_KEYWORDS = void 0;
const wiaCommandRegistry_1 = require("../registry/wiaCommandRegistry");
exports.COMMAND_DOMAIN_KEYWORDS = {
    architecture: ['architecture', 'architectural', 'boundaries', 'subsystems', 'structure', 'map', 'components', 'design'],
    deps: ['deps', 'dependencies', 'dependency', 'package', 'packages', 'conflicts', 'manifest', 'manifests'],
    doctor: ['doctor', 'diagnostics', 'diagnostic', 'environment', 'health', 'system', 'diagnostix'],
    status: ['status', 'indexing', 'changes', 'modified', 'index'],
    index: ['index', 'indexing', 'scan', 'reindex', 'rebuild'],
    test: ['test', 'tests', 'testz', 'pytest', 'testing', 'suite', 'unit', 'jest'],
    run: ['run', 'start', 'launch', 'serve', 'server', 'dev'],
    build: ['build', 'compile', 'bundle', 'package', 'dist'],
    summary: ['summary', 'summarize', 'overview', 'codebase'],
    security: ['security', 'secrets', 'secret', 'tokens', 'credentials', 'passwords', 'vulnerabilities', 'scanner'],
    git: ['git', 'churn', 'hotspots', 'commits', 'history'],
    diff: ['diff', 'changes', 'changed'],
    report: ['report', 'html', 'export'],
    search: ['search', 'find', 'lookup', 'symbol'],
    explain: ['explain', 'purpose', 'function', 'class'],
    impact: ['impact', 'blast', 'radius', 'callers', 'affected'],
    flow: ['flow', 'trace', 'hierarchy', 'call'],
    files: ['files', 'list', 'indexed'],
    info: ['info', 'tech', 'stack', 'languages', 'frameworks'],
    config: ['config', 'settings', 'provider', 'key']
};
/**
 * JEV (Jaccard, Edit-Distance, Vector) Hybrid Scoring Module for non-autoregressive routing.
 */
class JEVRouter {
    /**
     * Compute Soft Jaccard token similarity with Candidate Containment & fuzzy token matching
     */
    static computeJaccard(queryTokens, candTokens) {
        if (queryTokens.size === 0 && candTokens.size === 0)
            return 1.0;
        if (queryTokens.size === 0 || candTokens.size === 0)
            return 0.0;
        let softMatches = 0;
        for (const c of candTokens) {
            for (const q of queryTokens) {
                if (q === c || this.computeEditSimilarity(q, c) >= 0.75) {
                    softMatches++;
                    break;
                }
            }
        }
        const union = Math.max(1, queryTokens.size + candTokens.size - softMatches);
        const jaccard = softMatches / union;
        const containment = softMatches / candTokens.size;
        return (0.4 * jaccard) + (0.6 * containment);
    }
    /**
     * Compute Levenshtein distance normalized similarity: 1 - dist / max(lenA, lenB)
     */
    static computeEditSimilarity(strA, strB) {
        if (strA === strB)
            return 1.0;
        const lenA = strA.length;
        const lenB = strB.length;
        if (lenA === 0)
            return lenB === 0 ? 1.0 : 0.0;
        if (lenB === 0)
            return 0.0;
        const matrix = [];
        for (let i = 0; i <= lenA; i++) {
            matrix[i] = [i];
        }
        for (let j = 0; j <= lenB; j++) {
            matrix[0][j] = j;
        }
        for (let i = 1; i <= lenA; i++) {
            for (let j = 1; j <= lenB; j++) {
                const cost = strA[i - 1] === strB[j - 1] ? 0 : 1;
                matrix[i][j] = Math.min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + cost);
            }
        }
        const dist = matrix[lenA][lenB];
        const maxLen = Math.max(lenA, lenB);
        return Math.max(0, 1 - dist / maxLen);
    }
    /**
     * Compute weighted keyword vector vocabulary overlap with fuzzy keyword matching
     */
    static computeVectorScore(queryTokens, domainKeywords) {
        if (domainKeywords.length === 0)
            return 0.0;
        let matchCount = 0;
        for (const kw of domainKeywords) {
            const cleanKw = kw.toLowerCase();
            for (const q of queryTokens) {
                if (q === cleanKw || this.computeEditSimilarity(q, cleanKw) >= 0.8) {
                    matchCount++;
                    break;
                }
            }
        }
        return Math.min(1.0, matchCount / Math.max(1, Math.min(domainKeywords.length, 2)));
    }
    /**
     * Compute composite JEV score: 0.35 * Jaccard + 0.35 * Edit + 0.30 * Vector
     */
    static evaluateJEV(query, candidate, domainKeywords = []) {
        const cleanQuery = query.toLowerCase().replace(/[^\w\s]/g, ' ').trim();
        const cleanCand = candidate.toLowerCase().replace(/[^\w\s]/g, ' ').trim();
        const queryTokens = new Set(cleanQuery.split(/\s+/).filter(Boolean));
        const candTokens = new Set(cleanCand.split(/\s+/).filter(Boolean));
        const jaccard = this.computeJaccard(queryTokens, candTokens);
        const phraseEdit = this.computeEditSimilarity(cleanQuery, cleanCand);
        // Token alignment edit distance (handles typos inside multi-word queries)
        let editDistance = phraseEdit;
        const qArr = Array.from(queryTokens);
        const cArr = Array.from(candTokens);
        if (qArr.length > 0 && cArr.length > 0) {
            let tokenEditSum = 0;
            for (const q of qArr) {
                let maxT = 0;
                for (const c of cArr) {
                    const sim = this.computeEditSimilarity(q, c);
                    if (sim > maxT)
                        maxT = sim;
                }
                tokenEditSum += maxT;
            }
            const tokenAlignment = tokenEditSum / qArr.length;
            editDistance = Math.max(phraseEdit, tokenAlignment);
        }
        const vectorScore = this.computeVectorScore(queryTokens, domainKeywords.length > 0 ? domainKeywords : Array.from(candTokens));
        const compositeScore = (0.35 * jaccard) + (0.35 * editDistance) + (0.30 * vectorScore);
        return {
            jaccard,
            editDistance,
            vectorScore,
            compositeScore
        };
    }
}
exports.JEVRouter = JEVRouter;
class LayaDecisionEngine {
    jevThreshold = 0.58;
    /**
     * Route a natural-language query to a registered WIA command or AI fallback using JEV matching.
     */
    route(query, registry = wiaCommandRegistry_1.CANONICAL_WIA_COMMAND_REGISTRY, context) {
        const raw = query.trim();
        const normalized = raw.toLowerCase().replace(/[?!.,;:]+$/, '').trim();
        if (!raw) {
            return {
                route_type: 'ai_fallback',
                command: null,
                arguments: {},
                confidence: 0.0,
                reason: 'Empty query',
                rationale: 'No query provided.',
                requires_llm_reasoning: false
            };
        }
        // 1. Conceptual AI Reasoning Questions (Must route to AI fallback with grounded context)
        // Questions starting with "Why...", "Is this...", "Explain why...", "Explain the tradeoff...", "What is the best..."
        if (/^(why\s+|is\s+this\s+|should\s+i\s+|are\s+these\s+|can\s+we\s+|what\s+is\s+the\s+(best|tradeoff|trade-off|difference|pattern|way|approach)|what\s+are\s+the\s+(pros|cons|tradeoffs|trade-offs|advantages|differences))/i.test(raw) ||
            /\b(explain\s+why|explain\s+the\s+(tradeoff|trade-off|design|difference|relationship)|trade-offs\s+between|tradeoffs\s+between)\b/i.test(raw) ||
            /\b(how\s+does\s+.*\s+work\??|why\s+is\s+.*\s+(tightly\s+coupled|failing|designed|unusual|slow|complex))\b/i.test(raw) ||
            /\b(is\s+.*\s+(maintainable|scalable|idiomatic|safe|secure))\b/i.test(raw)) {
            return {
                route_type: 'ai_fallback',
                command: null,
                arguments: {},
                confidence: 0.94,
                reason: 'No registered WIA command matches the request. Routing to AI reasoning layer with grounded workspace context.',
                rationale: 'Reasoning over codebase architecture and patterns using grounded WIA workspace context.',
                requires_llm_reasoning: true
            };
        }
        // 2. Exact command name or alias match
        for (const [cmdName, def] of Object.entries(registry)) {
            if (normalized === cmdName || def.aliases.some(alias => normalized === alias.toLowerCase())) {
                const args = this.resolveCommandArguments(cmdName, raw, context);
                return {
                    route_type: 'wia_command',
                    command: cmdName,
                    arguments: args,
                    confidence: 0.99,
                    rationale: `Direct match with WIA command '${cmdName}' (${def.description})`,
                    requires_llm_reasoning: def.requires_llm,
                    extractedTarget: args.target || args.symbol || args.query || args.entry,
                    jevBreakdown: { jaccard: 1.0, editDistance: 1.0, vectorScore: 1.0, compositeScore: 1.0 }
                };
            }
        }
        // 3. High-precision semantic intent classifiers for registered WIA commands
        // A. Project Test Command
        if (/\b(run|execute|start)\b.*\b(test|tests|pytest|spec|suite|jest)\b|\b(run\s+tests|test\s+suite|run\s+the\s+tests|run\s+pytest)\b|^test$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'test',
                arguments: {},
                confidence: 0.98,
                rationale: 'Executing workspace automated test suite.',
                requires_llm_reasoning: false
            };
        }
        // B. Project Run Command
        if (/\b(how\s+(do\s+i|to)\s+)?(run|start|serve|launch|execute)\s+(this\s+)?(project|app|application|server|daemon|backend|frontend)\b|^run(\s+the\s+project)?$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'run',
                arguments: {},
                confidence: 0.96,
                rationale: 'Executing project run / development server command.',
                requires_llm_reasoning: false
            };
        }
        // C. Project Build Command
        if (/\b(build|compile|bundle|package|distribute|make)\s+(the\s+)?(project|app|binary|package|wheel|dist|code)\b|^build$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'build',
                arguments: {},
                confidence: 0.95,
                rationale: 'Executing project build / compile command.',
                requires_llm_reasoning: false
            };
        }
        // D. Git Diff Impact (Check before general impact)
        if (/\b(git\s+diff|git\s+changes|uncommitted\s+changes|diff\s+impact|audit\s+git)\b/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'diff',
                arguments: {},
                confidence: 0.96,
                rationale: 'Analyzing git diff and unstaged change impact.',
                requires_llm_reasoning: false
            };
        }
        // E. Impact Analysis (Requires symbol/target extraction)
        if (/\b(impact|blast\s+radius|who\s+calls|affected\s+symbols|downstream\s+impact)\b/i.test(raw)) {
            const sym = this.extractSymbolOrFile(raw, /\b(impact\s+of(\s+changing)?|blast\s+radius\s+of|who\s+calls|affect\s+if\s+i\s+change)\s+([A-Za-z0-9_./\\-]+)/i, context);
            return {
                route_type: 'wia_command',
                command: 'impact',
                arguments: { symbol: sym || 'WorkspaceIndex' },
                confidence: 0.96,
                rationale: `Analyzing refactoring blast radius and downstream callers for '${sym || 'target'}'.`,
                requires_llm_reasoning: false,
                extractedTarget: sym
            };
        }
        // E. Call Flow Trace
        if (/\b(call\s+flow|execution\s+flow|trace\s+flow|call\s+hierarchy|trace\s+execution)\b/i.test(raw)) {
            const entry = this.extractSymbolOrFile(raw, /\b(trace|flow|hierarchy)\s+(of|from|for)?\s+([A-Za-z0-9_./\\-]+)/i, context);
            return {
                route_type: 'wia_command',
                command: 'flow',
                arguments: { entry: entry || 'cli_entrypoint' },
                confidence: 0.95,
                rationale: `Tracing execution call flow hierarchy from '${entry || 'entrypoint'}'.`,
                requires_llm_reasoning: false,
                extractedTarget: entry
            };
        }
        // F. Explain Specific File or AST Symbol
        if (/\b(explain\s+(this\s+)?(file|function|symbol|class|method)|what\s+does\s+this\s+(file|function|symbol|code)\s+do|explain\s+([A-Za-z0-9_./\\-]+\.[a-z]+|[A-Za-z0-9_]{3,}))\b/i.test(raw) &&
            !/\b(why|tradeoff|difference|how)\b/i.test(raw)) {
            const target = this.extractSymbolOrFile(raw, /\b(explain|what\s+does)\s+(?:the\s+|this\s+)?(?:file\s+|function\s+|class\s+|symbol\s+)?([A-Za-z0-9_./\\-]+)/i, context);
            if (target && !/^(project|workspace|codebase|architecture|why|the)$/i.test(target)) {
                return {
                    route_type: 'wia_command',
                    command: 'explain',
                    arguments: { target },
                    confidence: 0.96,
                    rationale: `Explaining structure and purpose of code target '${target}'.`,
                    requires_llm_reasoning: true,
                    extractedTarget: target
                };
            }
        }
        // G. Search Symbols / Files
        if (/^(find|search|lookup)\s+(?:for\s+)?(?:symbol\s+|file\s+|class\s+|function\s+)?([A-Za-z0-9_./\\-]+)$/i.test(raw)) {
            const match = raw.match(/^(find|search|lookup)\s+(?:for\s+)?(?:symbol\s+|file\s+|class\s+|function\s+)?([A-Za-z0-9_./\\-]+)$/i);
            const queryTerm = match ? match[2].trim() : raw;
            return {
                route_type: 'wia_command',
                command: 'search',
                arguments: { query: queryTerm },
                confidence: 0.95,
                rationale: `Searching workspace index for '${queryTerm}'.`,
                requires_llm_reasoning: false,
                extractedTarget: queryTerm
            };
        }
        // H. Dependencies Analysis (`wia analyze deps`)
        if (/\b(check\s+(the\s+)?dependencies|dependencies|dependency\s+conflicts?|list\s+dependencies|show\s+packages|package\s+manifests?|dependency\s+clash)\b/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'deps',
                arguments: {},
                confidence: 0.97,
                rationale: 'Analyzing workspace package manifests, dependencies, and version conflicts.',
                requires_llm_reasoning: false
            };
        }
        // I. Doctor & Environment Diagnostics (`wia doctor`)
        if (/\b(doctor|diagnostics|environment\s+health|check\s+(the\s+)?environment|system\s+health|env\s+check)\b/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'doctor',
                arguments: {},
                confidence: 0.97,
                rationale: 'Running system diagnostics and environment health audit.',
                requires_llm_reasoning: false
            };
        }
        // J. Status (`wia status`)
        if (/\b(show\s+(the\s+)?(project\s+)?status|workspace\s+status|indexing\s+status|check\s+status|changes\s+since\s+last\s+index)\b|^status$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'status',
                arguments: {},
                confidence: 0.98,
                rationale: 'Retrieving workspace indexing status and pending file changes.',
                requires_llm_reasoning: false
            };
        }
        // K. Index (`wia index`)
        if (/\b(index(\s+the|\s+this)?\s+workspace|reindex|scan\s+workspace|index\s+repository|rebuild\s+index)\b|^index$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'index',
                arguments: {},
                confidence: 0.98,
                rationale: 'Running workspace indexing pipeline.',
                requires_llm_reasoning: false
            };
        }
        // L. Architecture Intelligence (`wia architecture`)
        if (/\b(show(\s+me)?\s+(the\s+)?architecture|show\s+project\s+architecture|project\s+architecture|analyze\s+architecture|component\s+boundaries|subsystems\s+map)\b|^(architecture|how\s+is\s+(this|the)\s+project\s+structured\??)$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'architecture',
                arguments: {},
                confidence: 0.98,
                rationale: 'Displaying workspace architecture boundaries, component map, and dependency flow.',
                requires_llm_reasoning: false
            };
        }
        // M. Files (`wia files`)
        if (/\b(list\s+(the\s+|all\s+)?files|show\s+(the\s+|all\s+)?files|indexed\s+files|all\s+files|repository\s+files)\b|^files$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'files',
                arguments: {},
                confidence: 0.96,
                rationale: 'Listing all indexed repository files.',
                requires_llm_reasoning: false
            };
        }
        // N. Info (`wia info`)
        if (/\b(tech\s+stack|frameworks|languages\s+used|workspace\s+info|project\s+info|show\s+(the\s+)?(tech\s+stack|info))\b|^info$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'info',
                arguments: {},
                confidence: 0.96,
                rationale: 'Displaying workspace tech stack and languages.',
                requires_llm_reasoning: false
            };
        }
        // O. Summary (`wia summary`)
        if (/\b(workspace\s+summary|summarize\s+codebase|codebase\s+summary|generate\s+summary|explain\s+(the\s+|this\s+)?(project|codebase|workspace)|what\s+is\s+this\s+project|project\s+overview|overview\s+of\s+(the\s+|this\s+)?project)\b|^summary$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'summary',
                arguments: {},
                confidence: 0.98,
                rationale: 'Generating structured codebase overview and intelligence summary.',
                requires_llm_reasoning: false
            };
        }
        // P. Git Diff (`wia diff`)
        if (/\b(git\s+diff|git\s+changes|changed\s+symbols|what\s+changed\s+in\s+git|show\s+git\s+changes)\b|^diff$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'diff',
                arguments: {},
                confidence: 0.96,
                rationale: 'Inspecting Git diff and affected AST symbols.',
                requires_llm_reasoning: false
            };
        }
        // Q. Git Churn Hotspots (`wia analyze git`)
        if (/\b(git\s+hotspots?|file\s+churn|commit\s+history|churn\s+hotspots?)\b/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'git',
                arguments: {},
                confidence: 0.95,
                rationale: 'Analyzing Git commit churn and hotspot files.',
                requires_llm_reasoning: false
            };
        }
        // R. Security Scanner (`wia analyze security`)
        if (/\b(security(\s+scan|\s+analysis)?|scan\s+secrets|secret\s+scan|hardcoded\s+(secrets|tokens|credentials)|credentials\s+scan|run\s+security\s+analysis)\b/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'security',
                arguments: {},
                confidence: 0.96,
                rationale: 'Scanning workspace for hardcoded credentials and exposed secrets.',
                requires_llm_reasoning: false
            };
        }
        // S. HTML Report (`wia report`)
        if (/\b(html\s+report|generate\s+(the\s+)?report|export\s+(the\s+)?report|create\s+(the\s+)?report)\b|^report$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'report',
                arguments: {},
                confidence: 0.95,
                rationale: 'Generating standalone HTML intelligence report.',
                requires_llm_reasoning: false
            };
        }
        // T. Settings / Config (`wia config`)
        if (/\b(configure\s+ai|api\s+key|provider\s+settings|ai\s+settings|change\s+model)\b|^config$/i.test(raw)) {
            return {
                route_type: 'wia_command',
                command: 'config',
                arguments: {},
                confidence: 0.95,
                rationale: 'Opening AI provider configuration settings.',
                requires_llm_reasoning: false
            };
        }
        // 4. JEV Non-Autoregressive Matcher for Fuzzy / Variant Queries
        let bestCommand = null;
        let bestJevScore = 0;
        let bestJevBreakdown;
        for (const [cmdName, def] of Object.entries(registry)) {
            const domainKeywords = exports.COMMAND_DOMAIN_KEYWORDS[cmdName] || [cmdName];
            // Check command name
            const nameJev = JEVRouter.evaluateJEV(raw, cmdName, domainKeywords);
            if (nameJev.compositeScore > bestJevScore) {
                bestJevScore = nameJev.compositeScore;
                bestCommand = cmdName;
                bestJevBreakdown = nameJev;
            }
            // Check aliases
            for (const alias of def.aliases) {
                const aliasJev = JEVRouter.evaluateJEV(raw, alias, domainKeywords);
                if (aliasJev.compositeScore > bestJevScore) {
                    bestJevScore = aliasJev.compositeScore;
                    bestCommand = cmdName;
                    bestJevBreakdown = aliasJev;
                }
            }
        }
        if (bestCommand && bestJevScore >= this.jevThreshold) {
            const def = registry[bestCommand];
            const args = this.resolveCommandArguments(bestCommand, raw, context);
            return {
                route_type: 'wia_command',
                command: bestCommand,
                arguments: args,
                confidence: Math.min(0.98, bestJevScore),
                rationale: `JEV routing match (${(bestJevScore * 100).toFixed(1)}% similarity) for WIA command '${bestCommand}' (${def?.description || bestCommand})`,
                requires_llm_reasoning: def?.requires_llm || false,
                extractedTarget: args.target || args.symbol || args.query || args.entry,
                jevBreakdown: bestJevBreakdown
            };
        }
        // 5. UNKNOWN / GENERAL QUESTIONS -> AI FALLBACK
        return {
            route_type: 'ai_fallback',
            command: null,
            arguments: {},
            confidence: 0.92,
            reason: 'No registered WIA command matches the request. Routing to AI reasoning layer with grounded workspace context.',
            rationale: 'Synthesizing evidence-grounded AI answer using WIA retrieval context.',
            requires_llm_reasoning: true
        };
    }
    resolveCommandArguments(command, query, context) {
        const args = {};
        switch (command) {
            case 'explain':
                args.target = this.extractSymbolOrFile(query, /\b(explain|about)\s+([A-Za-z0-9_./\\-]+)/i, context) || (context?.activeFilePath || 'main.py');
                break;
            case 'impact':
                args.symbol = this.extractSymbolOrFile(query, /\b(impact\s+of|blast\s+radius\s+of|affecting)\s+([A-Za-z0-9_./\\-]+)/i, context) || (context?.activeSymbolName || context?.activeFilePath || 'WorkspaceIndex');
                break;
            case 'flow':
                args.entry = this.extractSymbolOrFile(query, /\b(flow\s+of|trace|hierarchy\s+for)\s+([A-Za-z0-9_./\\-]+)/i, context) || (context?.activeSymbolName || 'cli_entrypoint');
                break;
            case 'search': {
                const match = query.match(/\b(?:search|find|lookup)\s+(?:for\s+)?([A-Za-z0-9_./\\-]+)/i);
                args.query = match ? match[1].trim() : (context?.selectedText || query.trim());
                break;
            }
        }
        return args;
    }
    extractSymbolOrFile(query, pattern, context) {
        const match = query.match(pattern);
        if (match) {
            const extracted = match[match.length - 1].trim();
            if (extracted && !['file', 'function', 'class', 'symbol', 'this', 'the', 'project', 'workspace', 'why'].includes(extracted.toLowerCase())) {
                return extracted;
            }
        }
        if (context?.selectedText && context.selectedText.length < 80) {
            return context.selectedText.trim();
        }
        if (context?.activeSymbolName) {
            return context.activeSymbolName;
        }
        if (context?.activeFilePath) {
            return context.activeFilePath;
        }
        return undefined;
    }
    /**
     * Backward-compatibility wrapper for decide() method.
     */
    decide(query, context) {
        return this.route(query, wiaCommandRegistry_1.CANONICAL_WIA_COMMAND_REGISTRY, context);
    }
}
exports.LayaDecisionEngine = LayaDecisionEngine;
//# sourceMappingURL=layaEngine.js.map