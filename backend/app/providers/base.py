from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class LLMProvider(ABC):
    """Abstract base class for WIA LLM reasoning providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "You are WIA, an expert AI software architect.", **kwargs) -> str:
        """Generate response from grounded repository context."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials and endpoints are configured."""
        pass
