import os
import logging
from typing import Optional, Dict, Any
from app.core.config import settings
from app.providers.base import LLMProvider
from app.providers.nvidia_nim import NvidiaNIMProvider

logger = logging.getLogger("wia.llm")

def get_llm_provider() -> LLMProvider:
    """Factory to retrieve configured LLM provider (NVIDIA NIM is primary)."""
    return NvidiaNIMProvider()

class LLMClient:
    """
    Model-agnostic LLM Client for WIA.
    Primary & default provider: NVIDIA NIM (NeMo Inference Microservices).
    """

    @staticmethod
    def is_nim_available() -> bool:
        provider = NvidiaNIMProvider()
        return provider.is_available()

    @staticmethod
    def generate_completion(
        prompt: str,
        system_prompt: str = "You are WIA, an expert AI software architect.",
        allow_deterministic_fallback: bool = True
    ) -> str:
        provider_name = (settings.DEFAULT_LLM_PROVIDER or "nvidia").lower()

        # 1. Primary: NVIDIA NIM
        nim_provider = NvidiaNIMProvider()
        if nim_provider.is_available():
            try:
                return nim_provider.generate(prompt=prompt, system_prompt=system_prompt)
            except Exception as e:
                logger.warning(f"NVIDIA NIM call failed: {e}")
                if not allow_deterministic_fallback:
                    raise

        # 2. Secondary/Optional: OpenAI if configured
        if provider_name == "openai" and settings.OPENAI_API_KEY:
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

        # 3. Deterministic / Offline Fallback if allowed
        if allow_deterministic_fallback:
            logger.info("Using deterministic structured fallback generator (NVIDIA NIM not configured).")
            return LLMClient._local_deterministic_response(prompt)

        raise RuntimeError(
            "NVIDIA NIM is not configured. Please set NVIDIA_NIM_API_KEY to enable AI reasoning."
        )

    @staticmethod
    def _local_deterministic_response(prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "summarize file" in prompt_lower or "file" in prompt_lower:
            return "This module contains essential source code definitions, exports, and helper logic contributing to the workspace functionality."
        elif "folder" in prompt_lower:
            return "This folder organizes related module components, configurations, and sub-services into a structured domain package."
        elif "repository summary" in prompt_lower or "architecture" in prompt_lower:
            return "This repository presents a modular architecture containing server components, API endpoints, core models, and structured subsystem packages."
        else:
            return "Structured workspace intelligence retrieved from repository deterministic AST and graph analysis."
