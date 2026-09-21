"""WIA CLI `ask` command for grounded AI reasoning queries."""

import os
import sys
from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_kv
from wia.llm.service import LLMService, _load_env_file
from wia.storage.repository import IndexRepository


def _prompt_api_key_if_missing(api_key: str | None, offline: bool) -> tuple[str | None, bool]:
    """Interactive prompt for API key if missing and running in an interactive terminal."""
    if offline or api_key:
        return api_key, offline

    _load_env_file()
    from wia.llm.base import _get_stored_user_config
    cfg = _get_stored_user_config()

    existing_key = (
        cfg.get("ai_api_key")
        or os.getenv("NVIDIA_NIM_API_KEY")
        or os.getenv("NVIDIA_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )
    if existing_key:
        return existing_key, False

    # Check if running interactively
    if sys.stdin and sys.stdin.isatty():
        click.echo("\n" + click.style("🔑 No AI API Key detected (NVIDIA NIM / OpenAI / Gemini / Anthropic / Groq).", fg="yellow"))
        user_key = click.prompt(
            "Enter your LLM API Key (or press Enter for local offline intelligence)",
            default="",
            show_default=False,
            hide_input=True,
        ).strip()

        if user_key:
            if click.confirm("Save API Key to workspace .env file for future sessions?", default=False):
                env_path = Path.cwd() / ".env"
                var_name = "NVIDIA_NIM_API_KEY" if (user_key.startswith("nvapi-") or "nvidia" in user_key.lower()) else (
                    "ANTHROPIC_API_KEY" if user_key.startswith("sk-ant-") else (
                        "GEMINI_API_KEY" if user_key.startswith("AIzaSy") else "OPENAI_API_KEY"
                    )
                )
                try:
                    with open(env_path, "a", encoding="utf-8") as f:
                        f.write(f"\n{var_name}={user_key}\n")
                    click.echo(click.style(f"✅ Saved to {env_path}", fg="green"))
                except Exception as err:
                    click.echo(click.style(f"⚠️ Could not save to .env: {err}", fg="yellow"))
            return user_key, False

    return None, False


@click.command(name="ask", help="Ask AI reasoning agent a question grounded in workspace context.")
@click.argument("question")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
@click.option(
    "--api-key",
    "-k",
    type=str,
    default=None,
    help="LLM API Key (NVIDIA NIM, OpenAI, Gemini, Anthropic, Groq).",
)
@click.option(
    "--provider",
    "-p",
    type=str,
    default=None,
    help="LLM provider name: 'nvidia', 'openai', 'gemini', 'anthropic', 'groq', 'openrouter'.",
)
@click.option(
    "--model",
    "-m",
    type=str,
    default=None,
    help="Specific LLM model identifier.",
)
@click.option(
    "--offline",
    is_flag=True,
    help="Force local offline deterministic reasoning synthesizer without making network API calls.",
)
def ask_cmd(
    question: str,
    workspace: str | None,
    api_key: str | None,
    provider: str | None,
    model: str | None,
    offline: bool,
) -> None:
    """Query workspace reasoning agent with user prompt."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"WIA Workspace Reasoning for '{path.name}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before running reasoning queries."
            )
        )
        return

    resolved_key, is_offline = _prompt_api_key_if_missing(api_key, offline)

    service = LLMService(
        api_key=resolved_key,
        provider_name=provider,
        model=model,
        offline=is_offline,
    )
    answer = service.ask_question(question, index)

    click.echo(f"\n{click.style('Question:', bold=True)} {question}\n")
    click.echo(answer)
