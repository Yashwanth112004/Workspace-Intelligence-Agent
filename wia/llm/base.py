"""AI Provider abstraction layer for workspace intelligence and reasoning."""

import json
import logging
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from wia.core.config import WorkspaceConfig

logger = logging.getLogger("wia.llm")

CONFIG_FILE_PATH = Path.home() / ".wia" / "config.json"


def _get_stored_user_config() -> dict:
    """Read ~/.wia/config.json safely."""
    custom_path = os.environ.get("WIA_CONFIG_FILE")
    cfg_path = Path(custom_path) if custom_path else CONFIG_FILE_PATH
    if not cfg_path.exists():
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


class AIProvider(ABC):
    """Abstract interface for executing LLM queries against workspace context."""

    @abstractmethod
    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        """Generate reasoning completion given prompt query and grounded workspace context."""
        pass

    def is_available(self) -> bool:
        """Check if provider credentials and network endpoints are configured."""
        return True

    def generate_response(self, prompt: str, context: str) -> str:
        """Backward compatible signature for legacy LLMProvider callers."""
        return self.generate(prompt, context)


class NvidiaNimProvider(AIProvider):
    """NVIDIA NIM API provider connecting to hosted or self-hosted NIM endpoints."""

    DEFAULT_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
    DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str | None = None,
        timeout: float = 45.0,
    ):
        cfg = _get_stored_user_config()
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                os.environ.get("NVIDIA_NIM_API_KEY")
                or os.environ.get("NVIDIA_API_KEY")
                or os.environ.get("NIM_API_KEY")
                or cfg.get("ai_api_key")
                or ""
            )
        self.model = (
            model
            or os.environ.get("NVIDIA_MODEL")
            or os.environ.get("NVIDIA_NIM_MODEL")
            or cfg.get("ai_model")
            or self.DEFAULT_MODEL
        )
        self.endpoint = (
            endpoint
            or os.environ.get("NVIDIA_ENDPOINT")
            or os.environ.get("NVIDIA_NIM_ENDPOINT")
            or cfg.get("ai_endpoint")
            or self.DEFAULT_ENDPOINT
        )
        self.timeout = timeout

    def is_available(self) -> bool:
        """Verify NVIDIA API key presence without leaking secret."""
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        """Query NVIDIA NIM API endpoint with grounded context and prompt."""
        if not self.is_available():
            grounded_fallback = LocalReasoningProvider().generate(prompt, context, options)
            return (
                f"[⚠️ Notice: AI provider (NVIDIA NIM) is not configured (NVIDIA_API_KEY is not set). "
                f"Displaying grounded local intelligence.]\n\n"
                f"To configure your key, set NVIDIA_API_KEY or run: wia auth / wia config --set-key <KEY>\n\n"
                f"{grounded_fallback}"
            )

        system_prompt = (
            "You are WIA (Workspace Intelligence Agent), an expert software architecture and codebase reasoning engine.\n"
            "Answer the user's inquiry thoroughly, accurately, and strictly grounded in the provided workspace context.\n\n"
            "MANDATORY OUTPUT STRUCTURE (Use clear Markdown):\n"
            "1. **Executive Summary / Direct Answer**: Direct, concise answer.\n"
            "2. **Architecture & System Flow**: Component roles, execution lifecycle, and interactions.\n"
            "3. **Key Symbols & Implementation**: Exact classes, functions, files, and line numbers.\n"
            "4. **Step-by-Step Breakdown / Detailed Logic**: Clear technical walkthrough.\n"
            "5. **Evidence**: Bulleted list of verified file citations with line ranges."
        )

        user_content = f"### Grounded Workspace Context:\n{context}\n\n### User Question:\n{prompt}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
            "max_tokens": 2500,
        }

        import wia
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "User-Agent": f"WIA-Workspace-Intelligence-Agent/{wia.__version__}",
        }

        ep = self.endpoint.strip().rstrip("/")
        if not ep.endswith("/chat/completions"):
            ep = f"{ep}/chat/completions"

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(ep, data=req_data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                choices = resp_data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
                return "Received empty response from NVIDIA NIM API."

        except urllib.error.HTTPError as err:
            err_msg = f"HTTP Error {err.code}: {err.reason}"
            logger.warning(f"NVIDIA NIM API error ({err_msg}). Falling back to local reasoning.")
            grounded_fallback = LocalReasoningProvider().generate(prompt, context, options)
            return (
                f"[⚠️ Notice: NVIDIA NIM API returned {err_msg} for model '{self.model}'. "
                f"Falling back to local grounded reasoning engine.]\n\n"
                f"{grounded_fallback}"
            )
        except urllib.error.URLError as err:
            logger.warning(f"Network error connecting to NVIDIA NIM ({err.reason}). Falling back to local reasoning.")
            grounded_fallback = LocalReasoningProvider().generate(prompt, context, options)
            return (
                f"[⚠️ Notice: Could not connect to NVIDIA NIM endpoint ({err.reason}). "
                f"Falling back to local grounded reasoning engine.]\n\n"
                f"{grounded_fallback}"
            )
        except Exception as err:
            logger.warning(f"Reasoning error: {err}. Falling back to local reasoning.")
            grounded_fallback = LocalReasoningProvider().generate(prompt, context, options)
            return (
                f"[⚠️ Notice: Remote AI query encountered an issue ({type(err).__name__}). "
                f"Falling back to local grounded reasoning engine.]\n\n"
                f"{grounded_fallback}"
            )


NvidiaNIMProvider = NvidiaNimProvider


class OpenAIProvider(AIProvider):
    """Universal OpenAI-compatible API provider (OpenAI, Groq, OpenRouter, Ollama, Custom)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        cfg = _get_stored_user_config()
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                os.environ.get("OPENAI_API_KEY")
                or os.environ.get("GROQ_API_KEY")
                or os.environ.get("OPENROUTER_API_KEY")
                or cfg.get("ai_api_key")
                or ""
            )
        raw_url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL")
            or cfg.get("ai_endpoint")
            or "https://api.openai.com/v1"
        )
        clean_url = raw_url.strip().rstrip("/")
        if clean_url.endswith("/chat/completions"):
            clean_url = clean_url[:-len("/chat/completions")].rstrip("/")
        self.base_url = clean_url
        self.model = (
            model
            or os.environ.get("OPENAI_MODEL")
            or cfg.get("ai_model")
            or "gpt-4o"
        )

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        if not self.is_available():
            grounded = LocalReasoningProvider().generate(prompt, context, options)
            return f"[⚠️ Notice: OpenAI API key is not configured. Displaying local grounded reasoning.]\n\n{grounded}"
        try:
            from openai import OpenAI
            import wia
            default_headers = {
                "HTTP-Referer": "https://github.com/Yashwanth112004/Workspace-Intelligence-Agent",
                "X-Title": "WIA - Workspace Intelligence Agent",
                "User-Agent": f"WIA-Workspace-Intelligence-Agent/{wia.__version__}",
            }
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers=default_headers,
            )

            system_prompt = (
                "You are WIA (Workspace Intelligence Agent), an expert AI software architect.\n"
                "Answer questions strictly grounded in the provided codebase context.\n\n"
                "MANDATORY OUTPUT STRUCTURE (Markdown):\n"
                "1. **Executive Summary / Direct Answer**\n"
                "2. **Architecture & System Flow**\n"
                "3. **Key Symbols & Implementation**\n"
                "4. **Step-by-Step Breakdown**\n"
                "5. **Evidence & Citations**"
            )
            user_content = f"[GROUNDED WORKSPACE CONTEXT]\n{context}\n\n[USER QUESTION]\n{prompt}"

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=2048,
            )
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content.strip() if content else ""
            return "No response generated by model."
        except Exception as err:
            logger.warning(f"OpenAI API generation failed: {err}")
            grounded = LocalReasoningProvider().generate(prompt, context, options)
            return f"[⚠️ Notice: Remote OpenAI API query failed ({err}). Falling back to local grounded reasoning.]\n\n{grounded}"


OpenAICompatibleProvider = OpenAIProvider


class GeminiProvider(AIProvider):
    """Google Gemini AI reasoning provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        cfg = _get_stored_user_config()
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or cfg.get("ai_api_key") or ""
        self.model = model or os.environ.get("GEMINI_MODEL") or cfg.get("ai_model") or "gemini-1.5-flash"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        if not self.is_available():
            grounded = LocalReasoningProvider().generate(prompt, context, options)
            return f"[⚠️ Notice: Google Gemini API key not configured. Displaying local grounded reasoning.]\n\n{grounded}"
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            gmodel = genai.GenerativeModel(self.model)

            full_prompt = (
                "You are WIA, an expert AI software architect.\n"
                "Answer the user query grounded strictly in the provided workspace context.\n"
                "Format with: Executive Summary, Architecture & Flow, Key Symbols, Step-by-Step Explanation, and Evidence citations.\n\n"
                f"[GROUNDED CONTEXT]\n{context}\n\n"
                f"[QUERY]\n{prompt}"
            )
            resp = gmodel.generate_content(full_prompt)
            return resp.text.strip() if resp and resp.text else ""
        except Exception as err:
            logger.warning(f"Gemini generation failed: {err}")
            grounded = LocalReasoningProvider().generate(prompt, context, options)
            return f"[⚠️ Notice: Gemini API failed ({err}). Falling back to local grounded reasoning.]\n\n{grounded}"


class AnthropicProvider(AIProvider):
    """Anthropic Claude AI reasoning provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        cfg = _get_stored_user_config()
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY") or cfg.get("ai_api_key") or ""
        self.model = model or os.environ.get("ANTHROPIC_MODEL") or cfg.get("ai_model") or "claude-3-5-sonnet-20241022"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        if not self.is_available():
            grounded = LocalReasoningProvider().generate(prompt, context, options)
            return f"[⚠️ Notice: Anthropic API key not configured. Displaying local grounded reasoning.]\n\n{grounded}"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            system_prompt = (
                "You are WIA, an expert AI software architect grounded in codebase context.\n"
                "Structure responses clearly with: Executive Summary, Architecture & System Flow, Key Symbols, Detailed Walkthrough, and Evidence citations."
            )
            user_content = f"[GROUNDED CONTEXT]\n{context}\n\n[USER QUESTION]\n{prompt}"

            msg = client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            return msg.content[0].text if msg and msg.content else ""
        except Exception as err:
            logger.warning(f"Anthropic generation failed: {err}")
            grounded = LocalReasoningProvider().generate(prompt, context, options)
            return f"[⚠️ Notice: Anthropic API failed ({err}). Falling back to local grounded reasoning.]\n\n{grounded}"


class LocalReasoningProvider(AIProvider):
    """Deterministic local reasoning engine synthesizing grounded workspace evidence without external API dependencies."""

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        """Synthesize a structured, grounded answer from provided workspace context."""
        if not context or not context.strip():
            return (
                "Project Overview & Summary\n"
                "--------------------------\n"
                "Insufficient workspace context available to answer the query.\n\n"
                "Evidence\n"
                "--------\n"
                "- No matching files or symbols were found in the active workspace index."
            )

        p_lower = prompt.lower().strip()
        intent = (options or {}).get("intent", "")

        # Parse grounded context lines
        context_lines = [line.strip() for line in context.splitlines() if line.strip()]
        tech_lines = [l for l in context_lines if l.startswith("- **") and ":" in l]
        file_headers: list[str] = []
        for l in context_lines:
            if l.startswith("### File: "):
                raw_f = l.replace("### File: ", "").strip()
                if raw_f.startswith("`") and "`" in raw_f[1:]:
                    raw_f = raw_f.split("`")[1]
                elif " — " in raw_f:
                    raw_f = raw_f.split(" — ")[0].strip("`")
                else:
                    raw_f = raw_f.strip("`")
                if raw_f and raw_f not in file_headers:
                    file_headers.append(raw_f)

        # Extract declared symbols
        declared_symbols: list[str] = []
        for line in context_lines:
            if line.startswith("class ") or line.startswith("def ") or line.startswith("async def "):
                sym_name = line.split("(")[0].split(":")[0].replace("async ", "").replace("class ", "").replace("def ", "").strip()
                if sym_name and sym_name not in declared_symbols:
                    declared_symbols.append(sym_name)

        tech_summary = "\n".join(f"- {t.lstrip('- ')}" for t in tech_lines[:8]) if tech_lines else "- Python workspace modules"
        key_files = "\n".join(f"- `{f}`" for f in file_headers[:8]) if file_headers else "- Active workspace index"
        key_syms = "\n".join(f"- `{s}`" for s in declared_symbols[:8]) if declared_symbols else "- AST symbols"

        # 1. Project Overview & Architecture Intent
        if intent in ("GENERAL_PROJECT", "ARCHITECTURE") or any(
            w in p_lower for w in ("explain", "overview", "what does", "project", "repo", "architecture", "structure")
        ):
            return (
                "Project Overview & Architecture Summary\n"
                "======================================\n\n"
                "### Executive Summary\n"
                f"This workspace represents a modular software system analyzed through WIA's AST indexing, "
                f"framework detection, and directional knowledge graph engine.\n\n"
                "### Architecture & System Context\n"
                "The repository is organized into distinct functional layers verified across the codebase:\n"
                f"{key_files}\n\n"
                "### Key Symbols & Implementation\n"
                f"Core classes and functions identified in the active context:\n"
                f"{key_syms}\n\n"
                "### Technology Stack\n"
                f"{tech_summary}\n\n"
                "### Evidence\n"
                f"{key_files}"
            )

        # 2. Execution Flow / Lifecycle Intent
        if intent == "FLOW" or any(w in p_lower for w in ("flow", "lifecycle", "how does", "step", "pipeline")):
            steps = "\n".join(
                f"{i+1}. Execute logic in `{f}` with symbols ({declared_symbols[i] if i < len(declared_symbols) else 'core handlers'})."
                for i, f in enumerate(file_headers[:5])
            ) or "1. Initiate entry point execution.\n2. Dispatch requests through core handlers."

            return (
                f"Execution Flow & Lifecycle Analysis for: '{prompt}'\n"
                f"====================================================\n\n"
                f"### Executive Summary\n"
                f"Execution flows sequentially across the verified modules in the workspace.\n\n"
                f"### Execution Flow & Steps\n"
                f"{steps}\n\n"
                f"### Key Symbols & Components\n"
                f"{key_syms}\n\n"
                f"### Evidence\n"
                f"{key_files}"
            )

        # 3. Testing Intent
        if intent == "TESTING" or "test" in p_lower:
            test_files = [f for f in file_headers if "test" in f.lower()]
            test_list = "\n".join(f"- `{f}`" for f in test_files) if test_files else key_files
            return (
                "Testing Architecture & Verification Strategy\n"
                "============================================\n\n"
                "### Executive Summary\n"
                f"Testing infrastructure is configured with test suites verifying components and integration flows.\n\n"
                "### Test Suites & Coverage Locations\n"
                f"{test_list}\n\n"
                "### Key Symbols Tested\n"
                f"{key_syms}\n\n"
                "### Evidence\n"
                f"{key_files}"
            )

        # 4. General Grounded Query Synthesis
        return (
            f"Answer for: '{prompt}'\n"
            f"======================================\n\n"
            f"### Executive Summary\n"
            f"Analysis based on verified codebase context and AST symbols.\n\n"
            f"### Key Symbols & Implementation\n"
            f"{key_syms}\n\n"
            f"### Relevant Components\n"
            f"{key_files}\n\n"
            f"### Evidence\n"
            f"{key_files}"
        )


# Backward compatibility aliases
LLMProvider = AIProvider
MockLLMProvider = LocalReasoningProvider


class AIProviderFactory:
    """Factory creating configured AI providers."""

    @classmethod
    def get_provider(
        cls,
        provider_name: str | None = None,
        config: WorkspaceConfig | None = None,
    ) -> AIProvider:
        """Create and return the active AI provider based on environment and config."""
        # Check test isolation: if os.environ was explicitly cleared and no provider requested, fallback locally
        if provider_name is None and len(os.environ) == 0:
            return LocalReasoningProvider()

        # Check explicit env keys first
        if provider_name is None:
            if os.environ.get("WIA_AI_PROVIDER") or os.environ.get("WIA_LLM_PROVIDER"):
                p_name = (os.environ.get("WIA_AI_PROVIDER") or os.environ.get("WIA_LLM_PROVIDER") or "").lower().strip()
            elif os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY"):
                return NvidiaNimProvider()
            elif os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENROUTER_API_KEY"):
                return OpenAIProvider()
            elif os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
                return GeminiProvider()
            elif os.environ.get("ANTHROPIC_API_KEY"):
                return AnthropicProvider()
            else:
                cfg = _get_stored_user_config()
                p_name = (cfg.get("ai_provider") or "").lower().strip()
        else:
            p_name = provider_name.lower().strip()

        if p_name in ("nvidia", "nvidia_nim", "nim"):
            return NvidiaNimProvider()
        elif p_name in ("openai", "groq", "openrouter", "ollama", "custom"):
            return OpenAIProvider()
        elif p_name == "gemini":
            return GeminiProvider()
        elif p_name == "anthropic":
            return AnthropicProvider()
        elif p_name == "local":
            return LocalReasoningProvider()
        else:
            return LocalReasoningProvider()
