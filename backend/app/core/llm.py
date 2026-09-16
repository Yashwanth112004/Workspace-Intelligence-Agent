import os
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger("wia.llm")

class LLMClient:
    """Model-agnostic LLM Client supporting OpenAI, Anthropic, Gemini, NVIDIA Nemotron, and Fallback."""

    @staticmethod
    def generate_completion(prompt: str, system_prompt: str = "You are WIA, an expert AI software architect.") -> str:
        provider = settings.DEFAULT_LLM_PROVIDER.lower()

        # 1. Try Gemini
        if (provider in ("auto", "gemini")) and settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{system_prompt}\n\n{prompt}"
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API generation failed: {e}")

        # 2. Try OpenAI
        if (provider in ("auto", "openai")) and settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                return res.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"OpenAI API generation failed: {e}")

        # 3. Try Anthropic Claude
        if (provider in ("auto", "anthropic")) and settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                res = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return res.content[0].text.strip()
            except Exception as e:
                logger.warning(f"Anthropic API generation failed: {e}")

        # 4. Try NVIDIA Nemotron / OpenAI-compatible endpoint
        if (provider in ("auto", "nvidia")) and settings.NVIDIA_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(
                    base_url="https://integrate.api.nvidia.com/v1",
                    api_key=settings.NVIDIA_API_KEY
                )
                res = client.chat.completions.create(
                    model="nvidia/nemotron-4-340b-instruct",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                return res.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"NVIDIA API generation failed: {e}")

        # 5. Heuristic fallback when no API keys are present
        logger.info("Using local heuristic fallback generator for LLM call.")
        return LLMClient._local_heuristic_response(prompt)

    @staticmethod
    def _local_heuristic_response(prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "summarize file" in prompt_lower or "file" in prompt_lower:
            return "This module contains essential source code definitions, exports, and helper logic contributing to the workspace functionality."
        elif "folder" in prompt_lower:
            return "This folder organizes related module components, configurations, and sub-services into a structured domain package."
        elif "repository summary" in prompt_lower or "architecture" in prompt_lower:
            return "This repository presents a modular architecture containing server components, API endpoints, core models, and frontend client views."
        else:
            return "The workspace logic defines structured data entities and API interactions across the system modules."
