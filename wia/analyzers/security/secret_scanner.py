"""Security analyzer for static analysis and hardcoded secret detection with accelerated pre-filtering."""

import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class SecurityFinding:
    """Represents a detected security finding or hardcoded secret."""

    file_path: str
    line_number: int
    rule_id: str
    severity: str  # "HIGH", "CRITICAL", "MEDIUM", "LOW"
    description: str
    match_snippet: str
    classification: str = "REAL_SECRET"  # "REAL_SECRET", "SYNTHETIC_TEST_FIXTURE", "DOCUMENTATION_EXAMPLE"
    confidence: str = "HIGH"  # "HIGH", "MEDIUM", "LOW"

    def to_dict(self) -> dict:
        """Convert security finding to serializable dictionary."""
        return asdict(self)


class SecretScanner:
    """Scans source files for hardcoded secrets, API keys, and private tokens."""

    RULES: list[dict] = [
        {
            "rule_id": "SEC-001",
            "name": "AWS Access Key ID",
            "pattern": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
            "severity": "CRITICAL",
            "description": "Exposed AWS Access Key ID detected.",
            "quick_trigger": "AKIA",
        },
        {
            "rule_id": "SEC-002",
            "name": "RSA / Private Key",
            "pattern": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            "severity": "CRITICAL",
            "description": "Exposed Private Key block detected.",
            "quick_trigger": "PRIVATE KEY",
        },
        {
            "rule_id": "SEC-003",
            "name": "GitHub Personal Access Token",
            "pattern": re.compile(r"\b(ghp_[A-Za-z0-9]{36})\b"),
            "severity": "HIGH",
            "description": "Exposed GitHub Personal Access Token detected.",
            "quick_trigger": "ghp_",
        },
        {
            "rule_id": "SEC-004",
            "name": "Generic API Key Assignment",
            "pattern": re.compile(
                r"(?i)\b(api[_\-]?key|secret|token|password)\s*=\s*['\"]([A-Za-z0-9_\-]{16,})['\"]"
            ),
            "severity": "HIGH",
            "description": "Hardcoded API key or credential string assignment detected.",
            "quick_trigger": None,  # Check via general keywords
        },
        {
            "rule_id": "SEC-005",
            "name": "Slack Webhook URL",
            "pattern": re.compile(
                r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+"
            ),
            "severity": "MEDIUM",
            "description": "Exposed Slack Incoming Webhook URL detected.",
            "quick_trigger": "hooks.slack.com",
        },
    ]

    GENERAL_KEYWORDS = ("api", "key", "secret", "token", "pass", "akia", "private key", "ghp_", "slack")

    @classmethod
    def mask_secret(cls, text: str) -> str:
        """Mask middle portion of a detected secret snippet to prevent leaking sensitive cleartext."""
        if not text:
            return ""
        if len(text) <= 8:
            return "*" * len(text)
        return text[:4] + "*" * (len(text) - 8) + text[-4:]

    @classmethod
    def classify_finding(
        cls, file_path: str, line_str: str, raw_secret: str, full_content: str = ""
    ) -> tuple[str, str]:
        """Classify finding as REAL_SECRET, SYNTHETIC_TEST_FIXTURE, or DOCUMENTATION_EXAMPLE based on evidence."""
        norm_p = file_path.replace("\\", "/").lower()

        # 1. Check if match is in documentation
        if norm_p.endswith(".md") or norm_p.startswith("docs/"):
            return "DOCUMENTATION_EXAMPLE", "MEDIUM"

        # 2. Check if match is in test file
        if norm_p.startswith("tests/") or "test_" in norm_p or "_test." in norm_p:
            line_l = line_str.lower()
            # Evidence of synthetic scanner test fixtures
            synthetic_indicators = (
                "write_text",
                "secret_scanner",
                "test_security",
                "mock",
                "fake",
                "sample",
                "dummy",
                "akia...mple",
                "ghp_1234567890",
                "assert",
            )
            if any(ind in line_l or ind in full_content.lower() for ind in synthetic_indicators):
                return "SYNTHETIC_TEST_FIXTURE", "HIGH"

        return "REAL_SECRET", "HIGH"

    @classmethod
    def scan_content(cls, content: str, file_path: str = "") -> list[SecurityFinding]:
        """Scan string content for security rule violations with fast substring pre-filtering."""
        if not content:
            return []

        # Fast content-level pre-filter
        content_lower = content.lower()
        if not any(kw in content_lower for kw in cls.GENERAL_KEYWORDS):
            return []

        findings: list[SecurityFinding] = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            line_str = line.strip()
            if not line_str or (line_str.startswith("#") and "nosec" in line_str):
                continue

            line_lower = line.lower()
            for rule in cls.RULES:
                trigger = rule.get("quick_trigger")
                if trigger and trigger.lower() not in line_lower:
                    continue

                matches = rule["pattern"].finditer(line)
                for match in matches:
                    raw_val = match.group(0)
                    masked_secret = cls.mask_secret(raw_val)
                    masked_snippet = line.replace(raw_val, masked_secret).strip()

                    classification, confidence = cls.classify_finding(
                        file_path, line_str, raw_val, content
                    )

                    findings.append(
                        SecurityFinding(
                            file_path=file_path,
                            line_number=line_num,
                            rule_id=rule["rule_id"],
                            severity=rule["severity"],
                            description=rule["description"],
                            match_snippet=masked_snippet[:120],
                            classification=classification,
                            confidence=confidence,
                        )
                    )
        return findings

    @classmethod
    def scan_file(cls, file_path: str | Path) -> list[SecurityFinding]:
        """Scan a single file path for security findings."""
        path = Path(file_path)
        if not path.is_file():
            return []

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            return cls.scan_content(content, file_path=str(path))
        except Exception:
            return []

    @classmethod
    def scan_workspace(
        cls, workspace_path: str | Path, max_file_size_bytes: int = 2 * 1024 * 1024, files: list[Path] | None = None
    ) -> list[SecurityFinding]:
        """Discover and scan readable text files in workspace for security findings concurrently."""
        from concurrent.futures import ThreadPoolExecutor
        import os
        path = Path(workspace_path)
        findings: list[SecurityFinding] = []

        if files is not None:
            candidate_files = files
        else:
            ignored_parts = {
                ".wia",
                ".git",
                "node_modules",
                "venv",
                ".venv",
                ".pytest_cache",
                "__pycache__",
                "build",
                "dist",
                "wia-report.html",
            }
            candidate_files = []
            for p in path.rglob("*"):
                if not p.is_file():
                    continue
                if any(
                    part in ignored_parts
                    or part.endswith(".egg-info")
                    or part.endswith(".dist-info")
                    for part in p.parts
                ):
                    continue
                try:
                    if p.stat().st_size > max_file_size_bytes:
                        continue
                except OSError:
                    continue
                candidate_files.append(p)

        if not candidate_files:
            return []

        max_workers = min(32, (os.cpu_count() or 4) * 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(cls.scan_file, candidate_files)
            for file_findings in results:
                findings.extend(file_findings)

        return findings
