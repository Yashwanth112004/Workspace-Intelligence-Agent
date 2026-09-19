"""AI Provider abstraction layer for workspace intelligence and reasoning."""

import json
import logging
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Optional

from wia.core.config import WorkspaceConfig

logger = logging.getLogger("wia.llm")


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
    DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str | None = None,
        timeout: float = 45.0,
    ):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                os.environ.get("NVIDIA_NIM_API_KEY")
                or os.environ.get("NVIDIA_API_KEY")
                or os.environ.get("NIM_API_KEY")
                or ""
            )
        self.model = model or os.environ.get("NVIDIA_MODEL") or os.environ.get("NVIDIA_NIM_MODEL") or self.DEFAULT_MODEL
        self.endpoint = (
            endpoint
            or os.environ.get("NVIDIA_ENDPOINT")
            or os.environ.get("NVIDIA_NIM_ENDPOINT")
            or self.DEFAULT_ENDPOINT
        )
        self.timeout = timeout

    def is_available(self) -> bool:
        """Verify NVIDIA API key presence without leaking secret."""
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        """Query NVIDIA NIM API endpoint with grounded context and prompt."""
        if not self.is_available():
            return (
                "AI provider (NVIDIA NIM) is not configured.\n\n"
                "To enable AI reasoning, set the environment variable:\n"
                "  export NVIDIA_API_KEY='nvapi-...'\n\n"
                "Or configure it via:\n"
                "  wia config --set-key <YOUR_NVIDIA_API_KEY>\n\n"
                "Falling back to deterministic workspace retrieval analysis."
            )

        system_prompt = (
            "You are WIA (Workspace Intelligence Agent), an expert software architecture and codebase reasoning engine. "
            "Answer the user's inquiry thoroughly, accurately, and strictly grounded in the provided workspace context and code snippets. "
            "CRITICAL RULES:\n"
            "1. NEVER hallucinate, invent, or assume functions, classes, imports, callers, or architecture not supported by the workspace context.\n"
            "2. If evidence is missing or cannot be verified from the source files, explicitly state that evidence was not found.\n"
            "3. If inferring something, clearly prefix it with '[Inference]' or '[Likely]'.\n"
            "4. Always include an 'Evidence' section citing the verified file paths and line ranges.\n"
            "5. Structure the output clearly: Project Overview / Answer, Architecture / How it Works, Key Components, and Evidence."
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

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.endpoint, data=req_data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                choices = resp_data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
                return "Received empty response from NVIDIA NIM API."

        except urllib.error.HTTPError as err:
            err_msg = f"HTTP Error {err.code}: {err.reason}"
            if err.code == 401:
                return "Authentication Failed (401): The provided NVIDIA API key is invalid or expired. Check your NVIDIA_API_KEY."
            elif err.code == 429:
                return "Rate Limit Exceeded (429): NVIDIA NIM API rate limit reached. Please try again later."
            return f"NVIDIA NIM API error ({err_msg}). Ensure endpoint '{self.endpoint}' and model '{self.model}' are reachable."
        except urllib.error.URLError as err:
            return f"Network Error: Unable to connect to NVIDIA NIM endpoint ({err.reason})."
        except Exception as err:
            return f"Reasoning execution error: {type(err).__name__} occurred while querying AI provider."


NvidiaNIMProvider = NvidiaNimProvider


class OpenAIProvider(AIProvider):
    """Universal OpenAI-compatible API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o",
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or ""
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        if not self.is_available():
            return "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            system_prompt = (
                "You are WIA (Workspace Intelligence Agent), an expert AI software architect.\n"
                "Answer questions strictly grounded in the provided codebase context."
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
            return LocalReasoningProvider().generate(prompt, context)


OpenAICompatibleProvider = OpenAIProvider


class GeminiProvider(AIProvider):
    """Google Gemini AI reasoning provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or ""
        self.model = model or os.environ.get("GEMINI_MODEL") or "gemini-1.5-flash"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        if not self.is_available():
            return "Gemini API key not configured. Set GEMINI_API_KEY environment variable."
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            gmodel = genai.GenerativeModel(self.model)

            full_prompt = (
                f"You are WIA, an expert AI software architect.\n"
                f"Answer the user query grounded strictly in the provided workspace context.\n\n"
                f"[GROUNDED CONTEXT]\n{context}\n\n"
                f"[QUERY]\n{prompt}"
            )
            resp = gmodel.generate_content(full_prompt)
            return resp.text.strip() if resp and resp.text else ""
        except Exception as err:
            logger.warning(f"Gemini generation failed: {err}")
            return LocalReasoningProvider().generate(prompt, context)


class AnthropicProvider(AIProvider):
    """Anthropic Claude AI reasoning provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or ""
        self.model = model or os.environ.get("ANTHROPIC_MODEL") or "claude-3-5-sonnet-20241022"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        if not self.is_available():
            return "Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable."
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            system_prompt = "You are WIA, an expert AI software architect grounded in codebase context."
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
            return LocalReasoningProvider().generate(prompt, context)


class LocalReasoningProvider(AIProvider):
    """Deterministic local reasoning engine synthesizing grounded workspace evidence without external API dependencies."""

    def generate(self, prompt: str, context: str, options: dict[str, Any] | None = None) -> str:
        """Synthesize a structured, grounded answer from provided workspace context."""
        if not context or not context.strip():
            return (
                "Answer:\n"
                "Insufficient workspace context available to answer the query.\n\n"
                "Evidence:\n"
                "  * No matching files or symbols were found in the active workspace index."
            )

        p_lower = prompt.lower().strip()

        # Extract context lines for grounded synthesis
        context_lines = [l.strip() for l in context.splitlines() if l.strip()]
        tech_lines = [l for l in context_lines if l.startswith("- **") and ":" in l]
        file_headers = [l.replace("### File: ", "").strip("`") for l in context_lines if l.startswith("### File: ")]

        # 1. Project Overview & Architecture Queries
        if any(w in p_lower for w in ("explain the project", "overview", "what does this project do", "architecture", "what is this repo")):
            tech_summary = "\n".join(f"  * {t.lstrip('- ')}" for t in tech_lines[:8]) if tech_lines else "  * Python workspace components"
            key_files = "\n".join(f"  * `{f}`" for f in file_headers[:8]) if file_headers else "  * Indexed workspace modules"

            return (
                "Project Overview\n"
                "----------------\n"
                "This workspace is a software project analyzed through WIA's AST parsing and relationship graph.\n\n"
                "Architecture & Core Subsystems\n"
                "------------------------------\n"
                "The repository organizes its capabilities across modular components evidenced in the source tree:\n"
                f"{key_files}\n\n"
                "Technology Stack\n"
                "----------------\n"
                f"{tech_summary}\n\n"
                "Evidence\n"
                "--------\n"
                f"{key_files}"
            )

        # 2. General Query Grounded Synthesis
        top_files = "\n".join(f"  * `{f}`" for f in file_headers[:6]) if file_headers else "  * Active WorkspaceIndex & WorkspaceGraph"

        return (
            f"Answer\n"
            f"------\n"
            f"Analysis for query '{prompt}':\n\n"
            f"Relevant Components & Context\n"
            f"-----------------------------\n"
            f"{top_files}\n\n"
            f"Evidence\n"
            f"--------\n"
            f"{top_files}"
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
        p_name = (provider_name or os.environ.get("WIA_AI_PROVIDER") or os.environ.get("WIA_LLM_PROVIDER") or "").lower().strip()

        if p_name in ("nvidia", "nvidia_nim", "nim") or (not p_name and (os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY"))):
            return NvidiaNimProvider()
        elif p_name == "openai" or (not p_name and os.environ.get("OPENAI_API_KEY")):
            return OpenAIProvider()
        elif p_name == "gemini" or (not p_name and os.environ.get("GEMINI_API_KEY")):
            return GeminiProvider()
        elif p_name == "anthropic" or (not p_name and os.environ.get("ANTHROPIC_API_KEY")):
            return AnthropicProvider()
        else:
            return LocalReasoningProvider()
