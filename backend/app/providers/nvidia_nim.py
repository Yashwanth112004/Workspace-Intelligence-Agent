import os
import logging
from typing import Optional, Dict, Any
from app.providers.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger("wia.providers.nvidia_nim")

class NvidiaNIMProvider(LLMProvider):
    """
    NVIDIA NIM (NeMo Inference Microservices) Provider.
    Uses the OpenAI-compatible API format with NVIDIA NIM endpoints.
    Supported by NVIDIA API Catalog & self-hosted NIM microservices.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = settings.NVIDIA_NIM_API_KEY or settings.NVIDIA_API_KEY
        self.base_url = base_url or settings.NVIDIA_NIM_BASE_URL or "https://integrate.api.nvidia.com/v1"
        self.model = model or settings.NVIDIA_NIM_MODEL or "meta/llama-3.1-70b-instruct"


    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are WIA, an expert AI software architect.",
        **kwargs
    ) -> str:
        if not self.is_available():
            raise RuntimeError(
                "NVIDIA NIM is not configured. Please set the NVIDIA_NIM_API_KEY (or NVIDIA_API_KEY) "
                "environment variable or add it to your .env file."
            )

        try:
            from openai import OpenAI
            client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 2048)
            )
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content.strip() if content else ""
            return ""
        except Exception as e:
            # Redact any accidental tokens in logs/exceptions
            err_msg = str(e)
            if self.api_key and self.api_key in err_msg:
                err_msg = err_msg.replace(self.api_key, "[REDACTED_API_KEY]")
            logger.error(f"NVIDIA NIM generation failed: {err_msg}")
            raise RuntimeError(f"NVIDIA NIM API error: {err_msg}")
