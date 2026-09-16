import re
import logging
from typing import List, Tuple

logger = logging.getLogger("wia.security")

# Sensitive file patterns to completely ignore
SENSITIVE_FILES = {
    ".env", ".env.local", ".env.production", ".env.staging",
    "id_rsa", "id_ed25519", "id_dsa", ".pem", ".key", ".pkcs12", ".pfx",
    "credentials.json", "service-account.json", "auth.token", "secret.yaml"
}

# Regex patterns for detecting and redacting secrets in code
SECRET_PATTERNS = [
    (re.compile(r"""(?i)(?:api_key|apikey|secret_key|secret|token|password|auth_token|access_token|private_key)\s*[:=]\s*['"]([a-zA-Z0-9_\-\.\~]{12,})['"]"""), "[REDACTED_SECRET]"),
    (re.compile(r"""(?i)(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|glpat-[a-zA-Z0-9]{20,}|xox[baprs]-[a-zA-Z0-9]{10,})"""), "[REDACTED_API_TOKEN]"),
    (re.compile(r"""(?i)(?:AIza[0-9A-Za-z-_]{35})"""), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"""-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"""), "[REDACTED_PRIVATE_KEY]")
]

class SecretSafetyService:
    """Detects and redacts sensitive credentials, tokens, and private keys."""

    @staticmethod
    def is_sensitive_file(file_name: str) -> bool:
        """Returns True if the file name/extension represents a credential/secret file."""
        name_lower = file_name.lower()
        if name_lower in SENSITIVE_FILES:
            return True
        for sens in SENSITIVE_FILES:
            if sens.startswith(".") and name_lower.endswith(sens):
                return True
        return False

    @staticmethod
    def sanitize_content(text: str) -> str:
        """Scans code text and redacts API keys, passwords, and private keys."""
        if not text:
            return ""
        sanitized = text
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized
