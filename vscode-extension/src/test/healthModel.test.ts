/**
 * Health Model & Diagnostic Badge Verification Tests
 *
 * Verifies all 8 requirement cases for issue count and workspace health calculation.
 */

import { WorkspaceHealthReport, WorkspaceIssue } from '../executor/wiaExecutor';

export function calculateHealthUI(health: WorkspaceHealthReport, projectMeta?: { name?: string; hasLockfile?: boolean; aiAvailable?: boolean }) {
    const errors = health.errors || [];
    const warnings = health.warnings || [];
    const allIssues = [...errors, ...warnings];
    const totalIssues = allIssues.length;
    
    // Status and isHealthy are strictly computed from actual issue items
    const isHealthy = totalIssues === 0;

    const headerBadge = isHealthy
        ? '● Ready'
        : errors.length > 0
            ? `✕ ${errors.length} ${errors.length === 1 ? 'Error' : 'Errors'}`
            : `⚠ ${warnings.length} ${warnings.length === 1 ? 'Issue' : 'Issues'}`;

    const summaryBadge = isHealthy
        ? '✓ Workspace Healthy'
        : errors.length > 0
            ? `✕ ${totalIssues} ${totalIssues === 1 ? 'Error' : 'Errors'}`
            : `⚠ ${totalIssues} ${totalIssues === 1 ? 'Issue' : 'Issues'}`;

    return {
        isHealthy,
        totalIssues,
        headerBadge,
        summaryBadge,
        issues: allIssues
    };
}

// Test Runner
export function runHealthModelTests(): { passed: number; failed: number; results: string[] } {
    const results: string[] = [];
    let passed = 0;
    let failed = 0;

    function assert(cond: boolean, desc: string) {
        if (cond) {
            passed++;
            results.push(`✓ PASS: ${desc}`);
        } else {
            failed++;
            results.push(`✕ FAIL: ${desc}`);
        }
    }

    // Case 1: No errors, No warnings
    {
        const h: WorkspaceHealthReport = { status: 'healthy', errors: [], warnings: [], info: [] };
        const ui = calculateHealthUI(h);
        assert(ui.isHealthy === true, 'Case 1: isHealthy is true when no errors/warnings');
        assert(ui.headerBadge === '● Ready', 'Case 1: Header shows ● Ready');
        assert(ui.summaryBadge === '✓ Workspace Healthy', 'Case 1: Summary shows ✓ Workspace Healthy');
        assert(ui.totalIssues === 0, 'Case 1: Total issues is 0');
    }

    // Case 2: One real warning
    {
        const warning: WorkspaceIssue = {
            severity: 'warning',
            title: 'Dependency Conflict: sqlalchemy',
            message: "Package 'sqlalchemy' has conflicting specs: >=2.0.0, ==2.0.36",
            source: 'wia analyze deps',
            evidence: '[VERSION_MISMATCH] sqlalchemy: >=2.0.0, ==2.0.36',
            fix: 'Resolve version in requirements.txt'
        };
        const h: WorkspaceHealthReport = { status: 'warning', errors: [], warnings: [warning], info: [] };
        const ui = calculateHealthUI(h);
        assert(ui.isHealthy === false, 'Case 2: isHealthy is false with warning');
        assert(ui.headerBadge === '⚠ 1 Issue', 'Case 2: Header badge shows ⚠ 1 Issue');
        assert(ui.issues.length === 1 && ui.issues[0].title === 'Dependency Conflict: sqlalchemy', 'Case 2: Exact warning is accessible');
        assert(Boolean(ui.issues[0].evidence && ui.issues[0].source && ui.issues[0].fix), 'Case 2: Full issue metadata present');
    }

    // Case 3: One real error
    {
        const error: WorkspaceIssue = {
            severity: 'error',
            title: 'System Diagnostic Error',
            message: 'SQLite database corruption detected',
            source: 'wia doctor',
            evidence: '[ERROR] SQLite database header invalid',
            fix: 'Run `wia index --force` to rebuild database'
        };
        const h: WorkspaceHealthReport = { status: 'error', errors: [error], warnings: [], info: [] };
        const ui = calculateHealthUI(h);
        assert(ui.isHealthy === false, 'Case 3: isHealthy is false with error');
        assert(ui.headerBadge === '✕ 1 Error', 'Case 3: Header badge shows ✕ 1 Error');
        assert(ui.issues.length === 1 && ui.issues[0].severity === 'error', 'Case 3: Exact error is accessible');
    }

    // Case 4: Three real issues
    {
        const i1: WorkspaceIssue = { severity: 'warning', title: 'Issue 1', message: 'M1', source: 'wia', evidence: 'E1' };
        const i2: WorkspaceIssue = { severity: 'warning', title: 'Issue 2', message: 'M2', source: 'wia', evidence: 'E2' };
        const i3: WorkspaceIssue = { severity: 'warning', title: 'Issue 3', message: 'M3', source: 'wia', evidence: 'E3' };
        const h: WorkspaceHealthReport = { status: 'warning', errors: [], warnings: [i1, i2, i3], info: [] };
        const ui = calculateHealthUI(h);
        assert(ui.headerBadge === '⚠ 3 Issues', 'Case 4: Header badge shows ⚠ 3 Issues');
        assert(ui.issues.length === 3, 'Case 4: All three issues are accessible');
    }

    // Case 5: Unknown project name -> No issue badge solely because project name is unknown
    {
        const h: WorkspaceHealthReport = { status: 'healthy', errors: [], warnings: [], info: [] };
        const ui = calculateHealthUI(h, { name: 'Unknown' });
        assert(ui.isHealthy === true, 'Case 5: Unknown project name does not produce an issue');
        assert(ui.totalIssues === 0, 'Case 5: Issue count remains 0');
    }

    // Case 6: No lockfile -> No issue badge solely because there is no lockfile
    {
        const h: WorkspaceHealthReport = { status: 'healthy', errors: [], warnings: [], info: [] };
        const ui = calculateHealthUI(h, { hasLockfile: false });
        assert(ui.isHealthy === true, 'Case 6: Missing lockfile is informational and does not produce an issue');
        assert(ui.totalIssues === 0, 'Case 6: Issue count remains 0');
    }

    // Case 7: AI provider unavailable -> Separate from workspace health
    {
        const h: WorkspaceHealthReport = { status: 'healthy', errors: [], warnings: [], info: [] };
        const ui = calculateHealthUI(h, { aiAvailable: false });
        assert(ui.isHealthy === true, 'Case 7: AI unavailable is not counted as a workspace health issue');
        assert(ui.totalIssues === 0, 'Case 7: Workspace health remains healthy');
    }

    // Case 8: Invariant check (Empty issue arrays MUST yield 0 count and healthy status)
    {
        const bogusHealth = { status: 'warning', errors: [], warnings: [], info: [] } as unknown as WorkspaceHealthReport;
        const ui = calculateHealthUI(bogusHealth);
        assert(ui.totalIssues === 0, 'Case 8: Empty issue arrays never manufacture issues');
        assert(ui.isHealthy === true, 'Case 8: Healthy when no actual issue objects exist');
        assert(ui.headerBadge === '● Ready', 'Case 8: Header displays ● Ready with 0 issues');
    }

    return { passed, failed, results };
}

// Execute if run directly via node
if (typeof require !== 'undefined' && require.main === module) {
    const res = runHealthModelTests();
    console.log(res.results.join('\n'));
    console.log(`\nTotal: ${res.passed} passed, ${res.failed} failed.`);
    if (res.failed > 0) process.exit(1);
}
