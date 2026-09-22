"""WIA CLI `config` and `auth` commands for managing user settings, AI providers, models, and endpoints."""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
import click

from wia.cli.formatting import format_header, format_kv, format_success, format_warning, format_error
from wia.llm.service import _load_env_file


CONFIG_FILE_PATH = Path.home() / ".wia" / "config.json"


PROVIDER_CATALOG: dict[str, dict[str, Any]] = {
    "nvidia": {
        "name": "NVIDIA NIM",
        "default_endpoint": "https://integrate.api.nvidia.com/v1",
        "default_model": "meta/llama-3.3-70b-instruct",
        "models": [
            ("meta/llama-3.3-70b-instruct", "Llama 3.3 70B Instruct (Recommended, State-of-the-Art)"),
            ("nvidia/llama-3.1-nemotron-70b-instruct", "NVIDIA Nemotron 70B (High Reasoning)"),
            ("meta/llama-3.1-70b-instruct", "Llama 3.1 70B Instruct"),
            ("meta/llama-3.1-8b-instruct", "Llama 3.1 8B Instruct (Ultra-Fast)"),
            ("mistralai/mistral-large-2-instruct", "Mistral Large 2 (123B)"),
        ],
        "env_var": "NVIDIA_NIM_API_KEY",
        "alt_env_vars": ["NVIDIA_API_KEY", "NIM_API_KEY"],
        "needs_key": True,
    },
    "openai": {
        "name": "OpenAI",
        "default_endpoint": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "models": [
            ("gpt-4o", "GPT-4o (Recommended, Flagship Omni Model)"),
            ("gpt-4o-mini", "GPT-4o Mini (Fast & Cost Efficient)"),
            ("o3-mini", "o3-mini (Advanced STEM & Code Reasoning)"),
            ("gpt-4-turbo", "GPT-4 Turbo"),
        ],
        "env_var": "OPENAI_API_KEY",
        "alt_env_vars": [],
        "needs_key": True,
    },
    "gemini": {
        "name": "Google Gemini",
        "default_endpoint": "https://generativelanguage.googleapis.com",
        "default_model": "gemini-1.5-flash",
        "models": [
            ("gemini-1.5-flash", "Gemini 1.5 Flash (Recommended, 1M Context Window)"),
            ("gemini-1.5-pro", "Gemini 1.5 Pro (Deep Code Reasoning)"),
            ("gemini-2.0-flash", "Gemini 2.0 Flash (Next-Gen Low Latency)"),
        ],
        "env_var": "GEMINI_API_KEY",
        "alt_env_vars": ["GOOGLE_API_KEY"],
        "needs_key": True,
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "default_endpoint": "https://api.anthropic.com/v1",
        "default_model": "claude-3-5-sonnet-20241022",
        "models": [
            ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet (Recommended, Top Architecture & Coding)"),
            ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku (Fast & Responsive)"),
            ("claude-3-opus-20240229", "Claude 3 Opus (Comprehensive Analysis)"),
        ],
        "env_var": "ANTHROPIC_API_KEY",
        "alt_env_vars": [],
        "needs_key": True,
    },
    "groq": {
        "name": "Groq Cloud",
        "default_endpoint": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            ("llama-3.3-70b-versatile", "Llama 3.3 70B Versatile (Recommended, High Throughput)"),
            ("llama-3.1-8b-instant", "Llama 3.1 8B Instant (Ultra-Low Latency)"),
            ("mixtral-8x7b-32768", "Mixtral 8x7B (32k Context)"),
        ],
        "env_var": "GROQ_API_KEY",
        "alt_env_vars": [],
        "needs_key": True,
    },
    "openrouter": {
        "name": "OpenRouter",
        "default_endpoint": "https://openrouter.ai/api/v1",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "models": [
            ("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B Instruct (Free Tier, Recommended)"),
            ("nvidia/llama-3.1-nemotron-70b-instruct:free", "NVIDIA Nemotron 70B (Free Tier)"),
            ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B Instruct"),
            ("deepseek/deepseek-r1:free", "DeepSeek R1 (Free Tier)"),
            ("deepseek/deepseek-chat", "DeepSeek V3 / R1"),
            ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet via OpenRouter"),
        ],
        "env_var": "OPENROUTER_API_KEY",
        "alt_env_vars": [],
        "needs_key": True,
    },
    "ollama": {
        "name": "Ollama / Local Server",
        "default_endpoint": "http://localhost:11434/v1",
        "default_model": "llama3.2",
        "models": [
            ("llama3.2", "Llama 3.2 (Default Local Model)"),
            ("qwen2.5-coder:7b", "Qwen 2.5 Coder 7B (Code Specialist)"),
            ("mistral", "Mistral 7B"),
            ("codellama", "Code Llama"),
        ],
        "env_var": "OLLAMA_API_KEY",
        "alt_env_vars": [],
        "needs_key": False,
    },
    "custom": {
        "name": "Custom OpenAI-Compatible API",
        "default_endpoint": "http://localhost:8000/v1",
        "default_model": "default",
        "models": [],
        "env_var": "CUSTOM_AI_API_KEY",
        "alt_env_vars": [],
        "needs_key": False,
    },
    "local": {
        "name": "Deterministic Local Reasoning (No API Key Required)",
        "default_endpoint": "",
        "default_model": "deterministic-ast-graph",
        "models": [],
        "env_var": "",
        "alt_env_vars": [],
        "needs_key": False,
    },
}


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


def _save_to_workspace_env(var_name: str, value: str) -> None:
    """Save environment variable to .env in current workspace directory."""
    if not var_name:
        return
    env_path = Path.cwd() / ".env"
    existing_lines = []
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        except Exception:
            existing_lines = []

    updated = False
    new_lines = []
    for line in existing_lines:
        if line.strip().startswith(f"{var_name}="):
            new_lines.append(f"{var_name}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{var_name}={value}\n")

    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception:
        pass


def test_provider_connection(
    provider_name: str,
    api_key: str,
    model: str,
    endpoint: str,
) -> tuple[bool, str, float]:
    """Perform a live verification test call to the configured provider endpoint."""
    p_info = PROVIDER_CATALOG.get(provider_name.lower(), {})
    if provider_name.lower() == "local":
        return True, "Local deterministic reasoning engine is active and ready.", 0.0

    target_endpoint = endpoint or p_info.get("default_endpoint", "")
    target_model = model or p_info.get("default_model", "")

    if not target_endpoint:
        return False, "No endpoint URL configured.", 0.0

    # Ensure direct HTTP POST points to /chat/completions for chat-compatible endpoints
    test_url = target_endpoint.strip().rstrip("/")
    if provider_name.lower() in ("openai", "openrouter", "groq", "ollama", "custom", "nvidia") and not test_url.endswith("/chat/completions"):
        test_url = f"{test_url}/chat/completions"

    import wia
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"WIA-Workspace-Intelligence-Agent/{wia.__version__}",
        "HTTP-Referer": "https://github.com/Yashwanth112004/Workspace-Intelligence-Agent",
        "X-Title": "WIA - Workspace Intelligence Agent",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    payload = {
        "model": target_model,
        "messages": [
            {"role": "user", "content": "Ping test from WIA"}
        ],
        "max_tokens": 5,
        "temperature": 0.1,
    }

    t0 = time.perf_counter()
    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(test_url, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            elapsed = round(time.perf_counter() - t0, 3)
            return True, f"Connection successful (HTTP {resp.status})", elapsed
    except urllib.error.HTTPError as err:
        elapsed = round(time.perf_counter() - t0, 3)
        if err.code == 401:
            return False, f"Authentication Failed (HTTP 401): API key is invalid or rejected by {p_info.get('name')}.", elapsed
        elif err.code == 404 or err.code == 410:
            return False, f"Model/Endpoint Not Found (HTTP {err.code}): Model '{target_model}' or endpoint is not available at {test_url}.", elapsed
        elif err.code == 429:
            return False, f"Rate Limit Exceeded (HTTP 429): Quota or rate limit exceeded.", elapsed
        return False, f"Provider returned HTTP {err.code}: {err.reason}", elapsed
    except urllib.error.URLError as err:
        elapsed = round(time.perf_counter() - t0, 3)
        return False, f"Network Connection Error: {err.reason}", elapsed
    except Exception as err:
        elapsed = round(time.perf_counter() - t0, 3)
        return False, f"Request failed: {err}", elapsed


def run_interactive_wizard() -> None:
    """Run interactive step-by-step configuration wizard for AI provider, key, model, and endpoint."""
    cfg = _load_user_config()

    click.echo(format_header("WIA AI Provider & Reasoning Configuration Wizard"))
    click.echo("Configure your AI model provider, API key, model ID, and endpoint.\n")

    # Step 1: Select Provider
    click.echo(click.style("Step 1: Select AI Reasoning Provider", bold=True))
    provider_keys = [
        "nvidia",
        "openai",
        "gemini",
        "anthropic",
        "groq",
        "openrouter",
        "ollama",
        "custom",
        "local",
    ]

    for idx, p_key in enumerate(provider_keys, start=1):
        p_data = PROVIDER_CATALOG[p_key]
        current_marker = " (Active)" if cfg.get("ai_provider") == p_key else ""
        click.echo(f"  {idx}. {p_data['name']}{click.style(current_marker, fg='green')}")

    choice_num = click.prompt(
        "\nSelect provider (1-9)",
        type=click.IntRange(1, len(provider_keys)),
        default=1,
    )
    selected_provider_key = provider_keys[choice_num - 1]
    provider_info = PROVIDER_CATALOG[selected_provider_key]

    if selected_provider_key == "local":
        cfg["ai_provider"] = "local"
        cfg["ai_model"] = "deterministic-ast-graph"
        cfg["ai_endpoint"] = ""
        _save_user_config(cfg)
        click.echo(format_success("Deterministic local reasoning activated. No API keys or remote calls required."))
        return

    # Step 2: API Key
    existing_key = cfg.get("ai_api_key") or os.getenv(provider_info.get("env_var", ""))
    for alt in provider_info.get("alt_env_vars", []):
        if not existing_key:
            existing_key = os.getenv(alt)

    click.echo(f"\n{click.style('Step 2: API Key Authentication', bold=True)}")
    if existing_key:
        masked = existing_key[:6] + "..." + existing_key[-4:] if len(existing_key) > 10 else "***"
        click.echo(f"Current API Key: {click.style(masked, fg='cyan')}")
        entered_key = click.prompt(
            f"Enter {provider_info['name']} API Key (press Enter to keep existing)",
            default=existing_key,
            show_default=False,
            hide_input=True,
        ).strip()
    else:
        entered_key = click.prompt(
            f"Enter {provider_info['name']} API Key",
            default="",
            show_default=False,
            hide_input=True,
        ).strip()

    # Step 3: Model Selection
    click.echo(f"\n{click.style('Step 3: Select Model Identifier', bold=True)}")
    models_list = provider_info.get("models", [])
    current_model = cfg.get("ai_model") or provider_info.get("default_model", "")

    if models_list:
        for idx, (m_id, m_desc) in enumerate(models_list, start=1):
            is_def = " (Default)" if m_id == provider_info.get("default_model") else ""
            click.echo(f"  {idx}. {click.style(m_id, bold=True)} — {m_desc}{is_def}")
        click.echo(f"  {len(models_list) + 1}. [Enter Custom Model ID]")

        model_choice = click.prompt(
            f"Select model (1-{len(models_list) + 1})",
            type=click.IntRange(1, len(models_list) + 1),
            default=1,
        )
        if model_choice <= len(models_list):
            selected_model = models_list[model_choice - 1][0]
        else:
            selected_model = click.prompt("Enter custom model ID", default=current_model).strip()
    else:
        selected_model = click.prompt(
            f"Enter model identifier for {provider_info['name']}",
            default=current_model or "default",
        ).strip()

    # Step 4: Endpoint URL
    click.echo(f"\n{click.style('Step 4: Endpoint URL Configuration', bold=True)}")
    default_endpoint = provider_info.get("default_endpoint", "")
    current_endpoint = cfg.get("ai_endpoint") or default_endpoint
    selected_endpoint = click.prompt(
        f"API Endpoint URL",
        default=current_endpoint,
    ).strip()

    # Step 5: Save Settings
    cfg["ai_provider"] = selected_provider_key
    if entered_key:
        cfg["ai_api_key"] = entered_key
    cfg["ai_model"] = selected_model
    cfg["ai_endpoint"] = selected_endpoint
    _save_user_config(cfg)

    # Also save to workspace .env if key is provided
    if entered_key and provider_info.get("env_var"):
        _save_to_workspace_env(provider_info["env_var"], entered_key)

    click.echo("\n" + format_success("Configuration saved successfully!"))
    click.echo(format_kv("Provider", provider_info['name']))
    click.echo(format_kv("Model", selected_model))
    click.echo(format_kv("Endpoint", selected_endpoint))
    click.echo(format_kv("Config File", str(CONFIG_FILE_PATH)))

    # Step 6: Test Connection
    if click.confirm("\nTest connection with configured provider now?", default=True):
        click.echo(f"Connecting to {selected_endpoint} with model '{selected_model}'...")
        success, msg, latency = test_provider_connection(
            provider_name=selected_provider_key,
            api_key=entered_key,
            model=selected_model,
            endpoint=selected_endpoint,
        )
        if success:
            click.echo(format_success(f"Connection Verified! Latency: {latency}s — {msg}"))
        else:
            click.echo(format_warning(f"Connection Check Notice: {msg}"))
            click.echo("You can modify settings anytime with 'wia config -i' or 'wia auth'.")


@click.command(name="config", help="View or configure AI providers, API keys, models, and endpoints.")
@click.option("--interactive", "-i", is_flag=True, help="Launch interactive configuration wizard.")
@click.option("--set-provider", "-p", help="Set default AI provider (e.g. nvidia, openai, gemini, anthropic, groq, openrouter, ollama, local).")
@click.option("--set-key", "-k", help="Set AI provider API key.")
@click.option("--set-model", "-m", help="Set default AI model identifier.")
@click.option("--set-endpoint", "-e", help="Set custom AI provider endpoint URL.")
@click.option("--show", "-s", is_flag=True, help="Display current AI and workspace configuration.")
@click.option("--test", "-t", is_flag=True, help="Test live connection to configured AI provider.")
@click.option("--clear-key", is_flag=True, help="Remove stored AI provider API key.")
def config_cmd(
    interactive: bool,
    set_provider: str | None,
    set_key: str | None,
    set_model: str | None,
    set_endpoint: str | None,
    show: bool,
    test: bool,
    clear_key: bool,
) -> None:
    """Manage WIA user configuration securely."""
    if interactive:
        run_interactive_wizard()
        return

    cfg = _load_user_config()
    changed = False

    if set_provider:
        p_clean = set_provider.lower().strip()
        cfg["ai_provider"] = p_clean
        # Automatically update default endpoint and model if switching provider unless already customized
        if p_clean in PROVIDER_CATALOG:
            if not cfg.get("ai_endpoint"):
                cfg["ai_endpoint"] = PROVIDER_CATALOG[p_clean].get("default_endpoint", "")
            if not cfg.get("ai_model"):
                cfg["ai_model"] = PROVIDER_CATALOG[p_clean].get("default_model", "")
        changed = True
        click.echo(format_success(f"Default AI provider set to '{cfg['ai_provider']}'"))

    if set_key:
        cfg["ai_api_key"] = set_key.strip()
        changed = True
        click.echo(format_success("AI API key saved successfully."))
        # Also sync to workspace .env
        active_p = cfg.get("ai_provider", "nvidia")
        env_var_name = PROVIDER_CATALOG.get(active_p, {}).get("env_var", "NVIDIA_NIM_API_KEY")
        _save_to_workspace_env(env_var_name, set_key.strip())

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

    # Connection Test
    if test:
        active_provider = cfg.get("ai_provider") or os.environ.get("WIA_AI_PROVIDER") or "nvidia"
        active_model = cfg.get("ai_model") or os.environ.get("NVIDIA_MODEL") or PROVIDER_CATALOG.get(active_provider, {}).get("default_model", "")
        active_endpoint = cfg.get("ai_endpoint") or os.environ.get("NVIDIA_ENDPOINT") or PROVIDER_CATALOG.get(active_provider, {}).get("default_endpoint", "")
        active_key = cfg.get("ai_api_key") or os.environ.get("NVIDIA_NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY") or ""

        click.echo(format_header("Testing AI Provider Connection"))
        click.echo(f"Provider: {active_provider} | Model: {active_model} | Endpoint: {active_endpoint}")
        success, msg, latency = test_provider_connection(active_provider, active_key, active_model, active_endpoint)
        if success:
            click.echo(format_success(f"Connection Verified! Latency: {latency}s — {msg}"))
        else:
            click.echo(format_error(f"Connection Failed: {msg}"))
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

    default_m = PROVIDER_CATALOG.get(active_provider, {}).get("default_model", "meta/llama-3.3-70b-instruct")
    active_model = cfg.get("ai_model") or os.environ.get("NVIDIA_MODEL") or default_m
    click.echo(format_kv("AI Model", active_model))

    default_ep = PROVIDER_CATALOG.get(active_provider, {}).get("default_endpoint", "https://integrate.api.nvidia.com/v1")
    active_endpoint = cfg.get("ai_endpoint") or os.environ.get("NVIDIA_ENDPOINT") or default_ep
    click.echo(format_kv("Endpoint", active_endpoint))
    click.echo(format_kv("Config File", str(CONFIG_FILE_PATH)))
    click.echo("\nTip: Run 'wia auth' or 'wia config -i' to launch the interactive setup wizard.")


@click.command(name="auth", help="Interactive setup wizard for AI provider, API key, model, and endpoint.")
def auth_cmd() -> None:
    """Interactive authentication wizard."""
    run_interactive_wizard()
