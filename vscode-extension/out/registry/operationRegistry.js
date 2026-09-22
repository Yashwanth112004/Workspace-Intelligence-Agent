"use strict";
/**
 * Controlled WIA Command and Operation Registry.
 *
 * All operations executed by Laya decisions or user queries MUST pass through this registry.
 * Arbitrary shell execution is strictly disallowed.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WIA_OPERATION_REGISTRY = void 0;
exports.isValidOperation = isValidOperation;
exports.getOperationDefinition = getOperationDefinition;
exports.WIA_OPERATION_REGISTRY = {
    // 1. Workspace Operations
    'workspace.scan': {
        name: 'workspace.scan',
        category: 'workspace',
        description: 'Scan and index workspace files, symbols, and dependencies',
        requiresTrust: true,
        isDestructive: false,
        cliSubcommand: 'index'
    },
    'workspace.summary': {
        name: 'workspace.summary',
        category: 'workspace',
        description: 'Retrieve structured facts and architectural intelligence summary',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'summary'
    },
    'workspace.status': {
        name: 'workspace.status',
        category: 'workspace',
        description: 'Check incremental change detection and indexing status',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'status'
    },
    // 2. Repository Operations
    'repository.structure': {
        name: 'repository.structure',
        category: 'repository',
        description: 'Analyze repository directory hierarchy and component layout',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'architecture'
    },
    'repository.files': {
        name: 'repository.files',
        category: 'repository',
        description: 'List all indexed repository files with language and classification',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'files'
    },
    'repository.languages': {
        name: 'repository.languages',
        category: 'repository',
        description: 'Get language distribution and framework detections',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'info'
    },
    'repository.frameworks': {
        name: 'repository.frameworks',
        category: 'repository',
        description: 'Inspect detected frameworks, build tools, and runtimes',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'info'
    },
    // 3. Index & Symbol Operations
    'index.search': {
        name: 'index.search',
        category: 'index',
        description: 'Search symbols, classes, functions, and docstrings via inverted index',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'search'
    },
    'index.symbols': {
        name: 'index.symbols',
        category: 'index',
        description: 'Query AST symbol index for definitions, line numbers, and docstrings',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'search'
    },
    'index.dependencies': {
        name: 'index.dependencies',
        category: 'index',
        description: 'Inspect cross-file import graph and symbol dependency links',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'impact'
    },
    // 4. Dependency Operations
    'dependency.list': {
        name: 'dependency.list',
        category: 'dependency',
        description: 'List manifest package dependencies across Python, Node, Cargo, Go',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'summary'
    },
    'dependency.check': {
        name: 'dependency.check',
        category: 'dependency',
        description: 'Check installed packages against manifest requirements and lockfiles',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'doctor'
    },
    'dependency.conflicts': {
        name: 'dependency.conflicts',
        category: 'dependency',
        description: 'Detect version mismatches and duplicate conflicting package definitions',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'doctor'
    },
    'dependency.missing': {
        name: 'dependency.missing',
        category: 'dependency',
        description: 'Identify uninstalled or missing declared manifest dependencies',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'doctor'
    },
    // 5. Environment Operations
    'environment.detect': {
        name: 'environment.detect',
        category: 'environment',
        description: 'Detect system runtimes, virtual environments, and package managers',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'doctor'
    },
    'environment.check': {
        name: 'environment.check',
        category: 'environment',
        description: 'Audit environment health, path configurations, and tool compatibility',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'doctor'
    },
    'environment.repair': {
        name: 'environment.repair',
        category: 'environment',
        description: 'Repair missing dependencies using detected project package manager',
        requiresTrust: true,
        isDestructive: false
    },
    // 6. Project Command Operations (Controlled execution)
    'project.run': {
        name: 'project.run',
        category: 'project',
        description: 'Execute detected project development or run command',
        requiresTrust: true,
        isDestructive: false
    },
    'project.build': {
        name: 'project.build',
        category: 'project',
        description: 'Execute detected project build command',
        requiresTrust: true,
        isDestructive: false
    },
    'project.test': {
        name: 'project.test',
        category: 'project',
        description: 'Execute detected project test suite command',
        requiresTrust: true,
        isDestructive: false
    },
    'project.lint': {
        name: 'project.lint',
        category: 'project',
        description: 'Execute detected project linter or typechecker command',
        requiresTrust: true,
        isDestructive: false
    },
    // 7. Architecture & Impact Operations
    'architecture.analyze': {
        name: 'architecture.analyze',
        category: 'architecture',
        description: 'Analyze subsystem boundaries, component coupling, fan-in/fan-out, and cycles',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'architecture'
    },
    'component.explain': {
        name: 'component.explain',
        category: 'component',
        description: 'Generate 13-section technical explanation for file, notebook, or symbol',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'explain'
    },
    'impact.analyze': {
        name: 'impact.analyze',
        category: 'impact',
        description: 'Compute refactoring blast radius, callers, dependents, and affected tests',
        requiresTrust: false,
        isDestructive: false,
        cliSubcommand: 'impact'
    }
};
function isValidOperation(opName) {
    return Object.prototype.hasOwnProperty.call(exports.WIA_OPERATION_REGISTRY, opName);
}
function getOperationDefinition(opName) {
    return exports.WIA_OPERATION_REGISTRY[opName];
}
//# sourceMappingURL=operationRegistry.js.map