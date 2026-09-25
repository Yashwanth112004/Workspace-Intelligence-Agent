"""CLI command for fast Laya decision routing."""

import json
import click
from wia.core.laya_router import get_laya_router


@click.command(name="decide")
@click.argument("query", type=str)
@click.option("--json", "json_output", is_flag=True, default=False, help="Output decision as JSON")
def decide_cmd(query: str, json_output: bool) -> None:
    """Determine which WIA operations to execute for a natural-language query using Laya."""
    engine = get_laya_router()
    decision = engine.decide(query)

    if json_output:
        click.echo(json.dumps(decision.to_dict(), indent=2))
        return

    click.echo("\n=== Laya Decision Engine ===")
    click.echo(f"  Request: {decision.request}")
    click.echo(f"  Intent: {decision.intent}")
    click.echo(f"  Confidence: {decision.confidence * 100:.1f}%")
    click.echo(f"  Requires LLM Reasoning: {'Yes' if decision.requires_llm_reasoning else 'No'}")
    click.echo("\n  Planned WIA Operations:")
    for op in decision.operations:
        param_str = f" ({op.parameters})" if op.parameters else ""
        click.echo(f"    -> {op.name}{param_str}")

    if decision.suggested_clarifications:
        click.echo("\n  Suggested Clarifications:")
        for c in decision.suggested_clarifications:
            click.echo(f"    - {c}")
    click.echo()
