/**
 * Canonical WIA Command Registry.
 *
 * Derived directly from the actual registered commands in the WIA CLI:
 * (wia/cli/app.py, wia/cli/commands/*.py, wia/core/architecture.py)
 *
 * This registry is the authoritative source for Laya routing and WIA execution.
 */

export interface WIACommandArgument {
    name: string;
    description: string;
    required: boolean;
    defaultValue?: any;
}

export interface WIACommandDefinition {
    name: string;
    description: string;
    aliases: string[];
    arguments: WIACommandArgument[];
    requires_llm: boolean;
    cliSubcommand: string[];
    category: 'architecture' | 'dependency' | 'environment' | 'workspace' | 'repository' | 'search' | 'project' | 'settings';
    isTerminalCommand?: boolean;
}

export const CANONICAL_WIA_COMMAND_REGISTRY: Record<string, WIACommandDefinition> = {
    // 0. AI Natural Language Query (wia ask)
    ask: {
        name: 'ask',
        description: 'Ask a natural language question about the codebase architecture, symbols, or flow.',
        aliases: [
            'ask',
            'ask agent',
            'query',
            'ask question'
        ],
        arguments: [
            { name: 'query', description: 'Natural language query or question', required: true },
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: true,
        cliSubcommand: ['ask'],
        category: 'workspace'
    },

    // 1. Architecture Intelligence
    architecture: {
        name: 'architecture',
        description: 'Display workspace architecture boundaries, component map, dependency flow, cycles, and hotspots.',
        aliases: [
            'architecture',
            'show architecture',
            'project architecture',
            'analyze architecture',
            'component boundaries',
            'subsystems',
            'system design',
            'how is this project structured',
            'project structure map',
            'show the architecture of this project',
            'show the architecture',
            'how is this project structured?'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['architecture'],
        category: 'architecture'
    },

    // 2. Dependencies & Conflicts
    deps: {
        name: 'deps',
        description: 'Analyze workspace package manifests, ecosystems, dependencies, and version conflicts.',
        aliases: [
            'dependencies',
            'deps',
            'check dependencies',
            'analyze dependencies',
            'dependency conflicts',
            'list dependencies',
            'show packages',
            'package manifests',
            'check the dependencies'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['analyze', 'deps'],
        category: 'dependency'
    },

    // 3. Status & Change Detection
    status: {
        name: 'status',
        description: 'Show current workspace index status, last indexed timestamp, and detected file changes.',
        aliases: [
            'status',
            'workspace status',
            'indexing status',
            'check status',
            'show status',
            'show the project status',
            'show project status',
            'index state',
            'changes since last index'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['status'],
        category: 'workspace'
    },

    // 4. Indexing Pipeline
    index: {
        name: 'index',
        description: 'Build or incrementally update the repository AST symbol index and graph.',
        aliases: [
            'index',
            'scan',
            'reindex',
            'index workspace',
            'index the workspace',
            'scan workspace',
            'index repository',
            'rebuild index',
            'index this workspace'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false },
            { name: 'force', description: 'Force complete re-indexing', required: false, defaultValue: false }
        ],
        requires_llm: false,
        cliSubcommand: ['index'],
        category: 'workspace'
    },

    // 5. Diagnostics & Environment Health
    doctor: {
        name: 'doctor',
        description: 'Run system diagnostics, verify Python/Node environments, PATH entries, and SQLite storage.',
        aliases: [
            'doctor',
            'environment',
            'check environment',
            'system health',
            'diagnostics',
            'env health',
            'system doctor',
            'verify environment',
            'check the environment'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['doctor'],
        category: 'environment'
    },

    // 6. Summary for RAG / Context
    summary: {
        name: 'summary',
        description: 'Generate structured facts, tech stack overview, and intelligence summary in Markdown.',
        aliases: [
            'summary',
            'workspace summary',
            'project summary',
            'summarize codebase',
            'codebase summary',
            'generate summary',
            'explain the project',
            'explain this project',
            'explain codebase',
            'explain workspace',
            'what is this project',
            'about this project',
            'project overview'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['summary'],
        category: 'workspace'
    },

    // 7. Files Directory
    files: {
        name: 'files',
        description: 'Display all indexed repository files with classifications and language filters.',
        aliases: [
            'files',
            'list files',
            'show files',
            'indexed files',
            'repository files',
            'all files',
            'show me the files'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false },
            { name: 'limit', description: 'Maximum files to show', required: false, defaultValue: 50 }
        ],
        requires_llm: false,
        cliSubcommand: ['files'],
        category: 'repository'
    },

    // 8. Info & Tech Stack
    info: {
        name: 'info',
        description: 'Display workspace language breakdown, detected frameworks, and entrypoints.',
        aliases: [
            'info',
            'workspace info',
            'tech stack',
            'languages',
            'frameworks',
            'project info',
            'about project'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['info'],
        category: 'repository'
    },

    // 9. Search Symbols & Files
    search: {
        name: 'search',
        description: 'Search workspace index for symbols, file paths, classes, or function names.',
        aliases: [
            'search',
            'find symbol',
            'find file',
            'lookup symbol',
            'search code',
            'find function',
            'find class'
        ],
        arguments: [
            { name: 'query', description: 'Search term or symbol identifier', required: true }
        ],
        requires_llm: false,
        cliSubcommand: ['search'],
        category: 'search'
    },

    // 10. Explain File or Symbol
    explain: {
        name: 'explain',
        description: 'Explain structure and purpose of a specific file or AST code symbol.',
        aliases: [
            'explain',
            'explain file',
            'explain symbol',
            'explain function',
            'explain class',
            'what does this file do',
            'what does this function do',
            'explain this file'
        ],
        arguments: [
            { name: 'target', description: 'File path or symbol name to explain', required: true }
        ],
        requires_llm: true,
        cliSubcommand: ['explain'],
        category: 'search'
    },

    // 11. Refactoring Impact Analysis
    impact: {
        name: 'impact',
        description: 'Evaluate downstream callers, blast radius, and risk of modifying a symbol or file.',
        aliases: [
            'impact',
            'blast radius',
            'impact of changing',
            'who calls',
            'affected symbols',
            'downstream impact',
            'refactoring impact',
            'show me the impact of changing'
        ],
        arguments: [
            { name: 'symbol', description: 'Symbol or file identifier to evaluate', required: true }
        ],
        requires_llm: false,
        cliSubcommand: ['impact'],
        category: 'architecture'
    },

    // 12. Call Flow Trace
    flow: {
        name: 'flow',
        description: 'Trace execution call flow hierarchy starting from an entry point or symbol.',
        aliases: [
            'flow',
            'call flow',
            'execution flow',
            'trace flow',
            'call hierarchy',
            'trace execution'
        ],
        arguments: [
            { name: 'entry', description: 'Entry point function or symbol to trace', required: true }
        ],
        requires_llm: false,
        cliSubcommand: ['flow'],
        category: 'architecture'
    },

    // 13. Git Diff & Changed Symbols
    diff: {
        name: 'diff',
        description: 'Analyze repository Git diff and identify affected AST symbols.',
        aliases: [
            'diff',
            'git diff',
            'changed symbols',
            'git changes',
            'what changed in git',
            'show diff'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['diff'],
        category: 'workspace'
    },

    // 14. Git Churn Hotspots
    git: {
        name: 'git',
        description: 'Analyze Git commit history and identify file churn hotspots.',
        aliases: [
            'git hotspots',
            'commit history',
            'file churn',
            'churn hotspots',
            'git churn'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['analyze', 'git'],
        category: 'repository'
    },

    // 15. Security & Secret Scanner
    security: {
        name: 'security',
        description: 'Scan workspace for hardcoded credentials, tokens, and security findings.',
        aliases: [
            'security',
            'security scan',
            'scan secrets',
            'secret scan',
            'check secrets',
            'credentials scan'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['analyze', 'security'],
        category: 'environment'
    },

    // 16. HTML Report Generator
    report: {
        name: 'report',
        description: 'Generate standalone HTML intelligence report for the repository.',
        aliases: [
            'report',
            'generate report',
            'html report',
            'export report',
            'create report'
        ],
        arguments: [
            { name: 'workspace', description: 'Workspace root directory path', required: false }
        ],
        requires_llm: false,
        cliSubcommand: ['report'],
        category: 'workspace'
    },

    // 17. Project Test Command
    test: {
        name: 'test',
        description: 'Execute project test suite (e.g. pytest, npm test, cargo test).',
        aliases: [
            'test',
            'run tests',
            'execute tests',
            'run pytest',
            'run test suite',
            'test project',
            'run unit tests',
            'run the tests'
        ],
        arguments: [],
        requires_llm: false,
        cliSubcommand: [],
        category: 'project',
        isTerminalCommand: true
    },

    // 18. Project Run Command
    run: {
        name: 'run',
        description: 'Execute project run/dev server command (e.g. npm start, python main.py).',
        aliases: [
            'run',
            'run project',
            'start project',
            'launch app',
            'how do i run this',
            'how to run',
            'how do i run this project?',
            'start server'
        ],
        arguments: [],
        requires_llm: false,
        cliSubcommand: [],
        category: 'project',
        isTerminalCommand: true
    },

    // 19. Project Build Command
    build: {
        name: 'build',
        description: 'Execute project build or packaging command (e.g. npm run build, tsc, cargo build).',
        aliases: [
            'build',
            'build project',
            'compile',
            'bundle',
            'build the project',
            'make'
        ],
        arguments: [],
        requires_llm: false,
        cliSubcommand: [],
        category: 'project',
        isTerminalCommand: true
    },

    // 20. AI Provider Configuration
    config: {
        name: 'config',
        description: 'Configure AI provider, models, and API keys.',
        aliases: [
            'config',
            'settings',
            'configure ai',
            'api key',
            'provider settings',
            'auth'
        ],
        arguments: [],
        requires_llm: false,
        cliSubcommand: ['config'],
        category: 'settings'
    }
};

export function getWIACommand(name: string): WIACommandDefinition | undefined {
    return CANONICAL_WIA_COMMAND_REGISTRY[name.toLowerCase()];
}

export function getAllWIACommands(): WIACommandDefinition[] {
    return Object.values(CANONICAL_WIA_COMMAND_REGISTRY);
}
