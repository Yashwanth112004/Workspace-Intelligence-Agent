"""WIA CLI `config` and `auth` commands for API key and provider configuration."""

import os
from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_kv, format_success
from wia.llm.service import _load_env_file


@click.group(name="config", help="Manage WIA workspace configuration and AI providers.")
def config_group() -> None:
    """Manage WIA workspace configuration and settings."""
    pass


@config_group.command(name="set-key", help="Set LLM API key in workspace .env file.")
@click.argument("provider", type=click.Choice(["nvidia", "openai", "gemini", "anthropic", "groq", "openrouter"], case_sensitive=False))
@click.argument("api_key", required=False)
def config_set_key(provider: str, api_key: str | None) -> None:
    """Store an LLM API key securely in .env."""
    if not api_key:
        api_key = click.prompt(f"Enter API Key for {provider}", hide_input=True).strip()

    var_map = {
        "nvidia": "NVIDIA_NIM_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    var_name = var_map[provider.lower()]

    env_path = Path.cwd() / ".env"
    existing_lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    # Update or append
    updated = False
    new_lines = []
    for line in existing_lines:
        if line.strip().startswith(f"{var_name}="):
            new_lines.append(f"{var_name}={api_key}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{var_name}={api_key}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    click.echo(format_success(f"Successfully saved {var_name} in {env_path.name}"))


@config_group.command(name="show", help="Display current AI provider and environment configuration.")
def config_show() -> None:
    """Show active environment variables and AI settings."""
    _load_env_file()
    click.echo(format_header("WIA AI Provider & Environment Status"))

    keys = [
        ("NVIDIA NIM Key", "NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY"),
        ("OpenAI Key", "OPENAI_API_KEY", None),
        ("Gemini Key", "GEMINI_API_KEY", None),
        ("Anthropic Key", "ANTHROPIC_API_KEY", None),
        ("Groq Key", "GROQ_API_KEY", None),
        ("OpenRouter Key", "OPENROUTER_API_KEY", None),
    ]

    for label, env_v, alt_v in keys:
        val = os.getenv(env_v) or (os.getenv(alt_v) if alt_v else None)
        if val:
            masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "***"
            status = click.style(f"Configured ({masked})", fg="green")
        else:
            status = click.style("Not set (Offline fallback available)", fg="yellow")
        click.echo(format_kv(label, status))

    click.echo(format_kv("Default Provider", os.getenv("WIA_LLM_PROVIDER") or "NVIDIA NIM (auto)"))


@click.command(name="auth", help="Interactive setup wizard for LLM provider API keys.")
def auth_cmd() -> None:
    """Interactive authentication wizard."""
    click.echo(format_header("WIA AI Provider Authentication Wizard"))
    click.echo("Select your preferred AI reasoning provider:\n")
    click.echo("  1. NVIDIA NIM (Recommended)")
    click.echo("  2. OpenAI (GPT-4o / GPT-4o-mini)")
    click.echo("  3. Google Gemini (Gemini 1.5 Flash/Pro)")
    click.echo("  4. Anthropic (Claude 3.5 Sonnet)")
    click.echo("  5. Groq / OpenRouter")
    click.echo("  6. Local Offline Reasoning (No API Key Required)\n")

    choice = click.prompt("Enter option (1-6)", type=click.IntRange(1, 6), default=1)
    provider_map = {1: "nvidia", 2: "openai", 3: "gemini", 4: "anthropic", 5: "groq"}

    if choice == 6:
        click.echo(click.style("✅ Local offline reasoning is ready. No API key needed.", fg="green"))
        return

    p_name = provider_map[choice]
    key = click.prompt(f"Enter your {p_name.upper()} API Key", hide_input=True).strip()
    if key:
        config_set_key.callback(provider=p_name, api_key=key)
