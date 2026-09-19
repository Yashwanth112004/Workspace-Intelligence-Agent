"""WIA CLI `config` and `auth` commands for managing user settings and AI provider configuration."""

import json
import os
from pathlib import Path
import click

from wia.cli.formatting import format_header, format_kv, format_success, format_warning
from wia.llm.service import _load_env_file


CONFIG_FILE_PATH = Path.home() / ".wia" / "config.json"


def _load_user_config() -> dict:
    """Load global user configuration from ~/.wia/config.json."""
    if not CONFIG_FILE_PATH.exists():
        return {}
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_user_config(cfg: dict) -> None:
    """Save global user configuration to ~/.wia/config.json."""
    CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


@click.command(name="config", help="View or configure AI providers, API keys, and models.")
@click.option("--set-provider", "-p", help="Set default AI provider (e.g. nvidia, openai, gemini, anthropic, groq, local).")
@click.option("--set-key", "-k", help="Set AI provider API key.")
@click.option("--set-model", "-m", help="Set default AI model identifier.")
@click.option("--set-endpoint", "-e", help="Set custom AI provider endpoint URL.")
@click.option("--show", is_flag=True, help="Display current AI and workspace configuration.")
@click.option("--clear-key", is_flag=True, help="Remove stored AI provider API key.")
def config_cmd(
    set_provider: str | None,
    set_key: str | None,
    set_model: str | None,
    set_endpoint: str | None,
    show: bool,
    clear_key: bool,
) -> None:
    """Manage WIA user configuration securely."""
    cfg = _load_user_config()
    changed = False

    if set_provider:
        cfg["ai_provider"] = set_provider.lower().strip()
        changed = True
        click.echo(format_success(f"Default AI provider set to '{cfg['ai_provider']}'"))

    if set_key:
        cfg["ai_api_key"] = set_key.strip()
        changed = True
        click.echo(format_success("AI API key saved successfully."))

    if set_model:
        cfg["ai_model"] = set_model.strip()
        changed = True
        click.echo(format_success(f"Default AI model set to '{cfg['ai_model']}'"))

    if set_endpoint:
        cfg["ai_endpoint"] = set_endpoint.strip()
        changed = True
        click.echo(format_success(f"AI endpoint set to '{cfg['ai_endpoint']}'"))

    if clear_key:
        if "ai_api_key" in cfg:
            del cfg["ai_api_key"]
            changed = True
            click.echo(format_success("Stored AI API key removed."))

    if changed:
        _save_user_config(cfg)
        return

    # Default: Show active configuration
    _load_env_file()
    click.echo(format_header("WIA Configuration"))

    active_provider = cfg.get("ai_provider") or os.environ.get("WIA_AI_PROVIDER") or os.environ.get("WIA_LLM_PROVIDER") or ("nvidia" if (os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY")) else "local")
    click.echo(format_kv("Active AI Provider", active_provider))

    env_key = (
        os.environ.get("NVIDIA_NIM_API_KEY")
        or os.environ.get("NVIDIA_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("GROQ_API_KEY")
    )
    stored_key = cfg.get("ai_api_key")

    if env_key:
        masked = env_key[:6] + "..." + env_key[-4:] if len(env_key) > 10 else "***"
        key_status = f"Configured via Environment Variable ({masked})"
    elif stored_key:
        masked = stored_key[:6] + "..." + stored_key[-4:] if len(stored_key) > 10 else "***"
        key_status = f"Configured in ~/.wia/config.json ({masked})"
    else:
        key_status = "Not Set (Set NVIDIA_API_KEY or use 'wia config --set-key')"

    click.echo(format_kv("API Key Status", key_status))

    active_model = cfg.get("ai_model") or os.environ.get("NVIDIA_MODEL") or "meta/llama-3.1-70b-instruct"
    click.echo(format_kv("AI Model", active_model))

    active_endpoint = cfg.get("ai_endpoint") or os.environ.get("NVIDIA_ENDPOINT") or "https://integrate.api.nvidia.com/v1/chat/completions"
    click.echo(format_kv("Endpoint", active_endpoint))
    click.echo(format_kv("Config File", str(CONFIG_FILE_PATH)))


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
        cfg = _load_user_config()
        cfg["ai_provider"] = p_name
        cfg["ai_api_key"] = key
        _save_user_config(cfg)
        click.echo(format_success(f"Successfully configured {p_name.upper()} API key."))
