"""WIA CLI `analyze` command group for dependencies, git history, and security findings."""

from pathlib import Path
import click
from wia.analyzers.dependency.conflict_detector import ConflictDetector
from wia.analyzers.dependency.manifest_parser import ManifestParser
from wia.analyzers.git.git_analyzer import GitAnalyzer
from wia.analyzers.security.secret_scanner import SecretScanner
from wia.cli.formatting import format_error, format_header, format_kv, format_success, format_warning


@click.group(name="analyze", help="Run workspace analysis tools (dependencies, git, security).")
def analyze_group() -> None:
    """Group for workspace analyzer subcommands."""
    pass


@analyze_group.command(name="deps", help="Analyze workspace package dependencies and version conflicts.")
@click.option("--workspace", "-w", type=click.Path(exists=True, file_okay=False, dir_okay=True), help="Path to workspace directory.")
def analyze_deps(workspace: str | None) -> None:
    """Analyze package dependencies and detect version conflicts."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Dependencies Analysis for '{path.name}'"))

    deps = ManifestParser.parse_workspace_manifests(path)
    if not deps:
        click.echo("No package manifest files (pyproject.toml, requirements.txt, package.json) found.")
        return

    manifests = sorted(set(item.manifest_path for item in deps))
    click.echo(click.style("Detected Dependency Manifests:", bold=True))
    for m in manifests:
        click.echo(f"  * {m}")

    click.echo()
    click.echo(format_kv("Total Dependencies Found", str(len(deps))))
    for item in deps:
        dep_type_str = f" [{item.dependency_type}]" if item.dependency_type else ""
        click.echo(f"  * {item.name} ({item.version_spec}) [{item.ecosystem}]{dep_type_str} in {item.manifest_path}")

    conflicts = ConflictDetector.detect_conflicts(deps)
    click.echo("\n" + format_header("Dependency Conflicts"))
    if not conflicts:
        click.echo(format_success("No dependency conflicts detected."))
    else:
        click.echo(format_warning(f"Found {len(conflicts)} conflict(s):"))
        for conflict in conflicts:
            click.echo(f"  ⚠️ [{conflict.conflict_type.upper()}] {conflict.package_name}: {conflict.reason}")


@analyze_group.command(name="git", help="Analyze Git history and identify file hotspots.")
@click.option("--workspace", "-w", type=click.Path(exists=True, file_okay=False, dir_okay=True), help="Path to workspace directory.")
@click.option("--max-commits", default=50, type=int, help="Maximum commits to analyze.")
@click.option("--top-hotspots", default=10, type=int, help="Number of top file hotspots to show.")
def analyze_git(workspace: str | None, max_commits: int, top_hotspots: int) -> None:
    """Analyze Git repository commits and churn hotspots."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Git Intelligence for '{path.name}'"))

    if not GitAnalyzer.is_git_repository(path):
        click.echo(format_warning(f"Directory '{path}' is not a valid Git repository."))
        return

    commits = GitAnalyzer.get_commit_history(path, max_commits=max_commits)
    click.echo(format_kv("Recent Commits Evaluated", str(len(commits))))

    hotspots = GitAnalyzer.get_file_hotspots(path, top_n=top_hotspots, max_commits=max_commits)
    click.echo("\n" + format_header(f"Top {len(hotspots)} Hotspots (File Churn)"))
    if not hotspots:
        click.echo("No commit churn data available.")
    else:
        for idx, spot in enumerate(hotspots, start=1):
            authors_str = ", ".join(spot.authors) if spot.authors else "Unknown"
            click.echo(f"  {idx}. {spot.path} ({spot.commit_count} commits by {authors_str})")


@analyze_group.command(name="security", help="Scan workspace for hardcoded secrets and security risks.")
@click.option("--workspace", "-w", type=click.Path(exists=True, file_okay=False, dir_okay=True), help="Path to workspace directory.")
def analyze_security(workspace: str | None) -> None:
    """Scan workspace for hardcoded secrets and exposed tokens."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Security Scan for '{path.name}'"))

    findings = SecretScanner.scan_workspace(path)
    if not findings:
        click.echo(format_success("No security findings or hardcoded secrets detected."))
        return

    real_findings = [f for f in findings if f.classification == "REAL_SECRET"]
    synthetic_findings = [f for f in findings if f.classification == "SYNTHETIC_TEST_FIXTURE"]
    doc_findings = [f for f in findings if f.classification == "DOCUMENTATION_EXAMPLE"]

    if real_findings:
        click.echo(format_error(f"Found {len(real_findings)} real security finding(s):"))
        for f in real_findings:
            sev_str = click.style(f"[{f.severity}]", fg="red", bold=True)
            click.echo(
                f"  {sev_str} {f.rule_id} in {f.file_path}:{f.line_number} -> {f.description}"
            )
            click.echo(f"     Snippet: {f.match_snippet}")
    else:
        click.echo(format_success("Security Findings: 0 (No real exposed credentials detected)"))

    if synthetic_findings:
        click.echo()
        click.echo(click.style(f"Synthetic Test Fixtures ({len(synthetic_findings)}):", bold=True, fg="bright_black"))
        click.echo("These matches occur in security scanner unit/integration tests and represent intentional test fixtures:")
        for f in synthetic_findings[:10]:
            fix_str = click.style(f"[{f.severity}]", fg="bright_black")
            click.echo(
                f"  {fix_str} {f.rule_id} in {f.file_path}:{f.line_number} -> {f.description}"
            )
            click.echo(f"     Snippet: {f.match_snippet}")
        if len(synthetic_findings) > 10:
            click.echo(f"  ... and {len(synthetic_findings) - 10} additional test fixture matches.")

    if doc_findings:
        click.echo()
        click.echo(click.style(f"Documentation Examples ({len(doc_findings)}):", bold=True, fg="bright_black"))
        for f in doc_findings[:5]:
            doc_str = click.style(f"[{f.severity}]", fg="cyan")
            click.echo(
                f"  {doc_str} {f.rule_id} in {f.file_path}:{f.line_number} -> {f.description}"
            )
            click.echo(f"     Snippet: {f.match_snippet}")
