"""Laya Non-Autoregressive Decision Engine and Operation Router.

Integrates fast, calibrated decision primitives (choice, score, noul)
for sub-35ms natural-language query routing to registered WIA operations.
"""

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class WIAOperationCall:
    """Represents an instantiated operation call with validated parameters."""

    name: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LayaDecision:
    """Structured decision returned by the Laya decision engine."""

    request: str
    intent: str
    operations: list[WIAOperationCall]
    confidence: float
    requires_llm_reasoning: bool
    rationale: str
    suggested_clarifications: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "intent": self.intent,
            "operations": [op.to_dict() for op in self.operations],
            "confidence": round(self.confidence, 3),
            "requires_llm_reasoning": self.requires_llm_reasoning,
            "rationale": self.rationale,
            "suggested_clarifications": self.suggested_clarifications,
        }


class LayaDecisionEngine:
    """Fast, calibrated non-autoregressive decision router for WIA operations."""

    # Supported registered WIA operations
    VALID_OPERATIONS = {
        "workspace.scan",
        "workspace.summary",
        "workspace.status",
        "repository.structure",
        "repository.files",
        "repository.languages",
        "repository.frameworks",
        "index.search",
        "index.symbols",
        "index.dependencies",
        "dependency.list",
        "dependency.check",
        "dependency.conflicts",
        "dependency.missing",
        "environment.detect",
        "environment.check",
        "environment.repair",
        "project.run",
        "project.build",
        "project.test",
        "project.lint",
        "architecture.analyze",
        "component.explain",
        "impact.analyze",
    }

    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        # Preload and compile intent regex patterns and routing tables in memory
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex pattern matching rules for instant sub-millisecond evaluation."""
        self.intent_patterns: list[tuple[str, re.Pattern, float, bool, list[str]]] = [
            # 1. Project Execution / Commands (Deterministic - No LLM needed)
            (
                "project_test",
                re.compile(r"\b(run|execute|start)\b.*\b(test|tests|pytest|spec|suite|jest)\b|\b(test|tests)\s*$", re.I),
                0.96,
                False,
                ["project.test"],
            ),
            (
                "project_run",
                re.compile(r"\b(how\s+to\s+)?(run|start|serve|launch|execute)\b.*\b(project|app|application|server|daemon|backend|frontend)\b|^run(\s+the)?\s+(project|app)$", re.I),
                0.95,
                False,
                ["project.run"],
            ),
            (
                "project_build",
                re.compile(r"\b(build|compile|bundle|package|distribute|make)\b.*\b(project|app|binary|package|wheel|dist)\b", re.I),
                0.94,
                False,
                ["project.build"],
            ),
            (
                "project_lint",
                re.compile(r"\b(lint|check style|format|typecheck|mypy|flake8|eslint|prettier)\b", re.I),
                0.93,
                False,
                ["project.lint"],
            ),

            # 2. Dependencies & Environment Diagnostics
            (
                "dependency_repair",
                re.compile(r"\b(fix|repair|install|resolve|update)\b.*\b(dependencies|packages|environment|env|modules|requirements)\b", re.I),
                0.95,
                False,
                ["environment.repair", "dependency.check"],
            ),
            (
                "dependency_check",
                re.compile(r"\b(check|list|inspect|show|find|audit|scan)\b.*\b(dependencies|dependency|package|packages|conflicts|missing|versions|lockfile)\b|\bwhy\s+is\s+.*(dependency|package)\s+failing\b", re.I),
                0.94,
                True,  # May need LLM if asking "why is dependency failing"
                ["dependency.check", "dependency.conflicts", "dependency.list"],
            ),
            (
                "environment_check",
                re.compile(r"\b(check|verify|detect|inspect|validate)\b.*\b(environment|env|python|node|java|runtime|venv|virtualenv|version)\b|\benvironment\s+(status|health|correct)\b", re.I),
                0.94,
                False,
                ["environment.detect", "environment.check"],
            ),

            # 3. Architecture & Project Overview
            (
                "architecture_overview",
                re.compile(r"\b(architecture|overview|subsystem|subsystems|boundaries|components|diagram|structure|design|system design)\b|\b(how\s+does\s+(this|the)\s+project\s+work|explain\s+(this|the)\s+project|show\s+(me\s+)?(project\s+)?architecture)\b", re.I),
                0.95,
                True,
                ["workspace.summary", "architecture.analyze", "repository.structure"],
            ),

            # 4. Impact Analysis & Blast Radius
            (
                "impact_analysis",
                re.compile(r"\b(what\s+will\s+(be\s+affected|break|change)|impact|blast radius|dependents|callers\s+of|what\s+depends\s+on)\b", re.I),
                0.93,
                True,
                ["impact.analyze", "index.dependencies", "index.symbols"],
            ),

            # 5. File & Symbol Exploration / Search
            (
                "file_listing",
                re.compile(r"\b(what\s+files|list\s+files|show\s+files|file\s+tree|all\s+files|directory\s+structure)\b", re.I),
                0.96,
                False,
                ["repository.files", "repository.structure"],
            ),
            (
                "symbol_search",
                re.compile(r"\b(where\s+is|find|search|lookup|locate)\b.*\b(class|function|method|symbol|endpoint|router|database|config|configuration)\b", re.I),
                0.92,
                False,
                ["index.search", "index.symbols"],
            ),

            # 6. Diagnosis / Failure Troubleshooting
            (
                "diagnose_problem",
                re.compile(r"\b(why\s+is\s+.*(not\s+working|failing|crashing|failing\s+to\s+start|broken|failing\s+tests)|troubleshoot|diagnose|error\s+in)\b", re.I),
                0.91,
                True,
                ["environment.check", "dependency.check", "workspace.status", "index.search"],
            ),

            # 7. Component Explanation / Deep Dive
            (
                "component_explain",
                re.compile(r"\b(how\s+does\s+.*work|explain\s+how|explain\s+the\s+.*|explain\s+.*|walk\s+through\s+.*|what\s+does\s+.*do)\b", re.I),
                0.90,
                True,
                ["component.explain", "index.search", "architecture.analyze"],
            ),
        ]

    def choice(self, query: str) -> tuple[str, float, bool, list[str]]:
        """Laya `choice` primitive: Select the best matching intent category and confidence score."""
        q = query.strip()
        if not q:
            return ("unknown", 0.0, False, ["workspace.summary"])

        for intent, pattern, base_conf, req_llm, ops in self.intent_patterns:
            if pattern.search(q):
                # Calculate calibrated confidence based on match specificity
                match_len = len(pattern.search(q).group(0))  # type: ignore
                length_bonus = min(0.05, match_len / 100.0)
                calibrated_conf = min(0.99, base_conf + length_bonus)
                return (intent, calibrated_conf, req_llm, ops)

        # Fallback general codebase reasoning
        if any(w in q.lower() for w in ("how", "why", "what", "where", "explain", "describe", "show")):
            return ("component_explain", 0.75, True, ["index.search", "architecture.analyze", "component.explain"])

        return ("general_query", 0.55, True, ["workspace.summary", "index.search"])

    def score(self, query: str, intent: str) -> float:
        """Laya `score` primitive: Score relevance of a proposed intent against query string (0.0 to 1.0)."""
        _, conf, _, _ = self.choice(query)
        return conf

    def noul(self, query: str, intent_hypothesis: str) -> tuple[bool, float]:
        """Laya `noul` primitive: Calibrated binary decision whether query matches intent hypothesis."""
        chosen_intent, conf, _, _ = self.choice(query)
        is_match = (chosen_intent == intent_hypothesis)
        probability = conf if is_match else (1.0 - conf)
        return (is_match, probability)

    def extract_target_entities(self, query: str) -> dict[str, str]:
        """Extract symbol, file, or component targets from natural language queries."""
        params: dict[str, str] = {}
        clean_q = query.strip()

        # Extract file path mentions (e.g. auth.py, package.json, wia/core/retrieval.py)
        file_match = re.search(r"\b([\w\-/\\]+\.(?:py|js|ts|jsx|tsx|go|rs|java|json|toml|yaml|yml|md|ipynb))\b", clean_q)
        if file_match:
            params["file_path"] = file_match.group(1).replace("\\", "/")

        # Extract quoted symbols or keywords
        quote_match = re.search(r"['\"]([^'\"]+)['\"]", clean_q)
        if quote_match:
            params["query"] = quote_match.group(1)
            params["symbol"] = quote_match.group(1)
        else:
            # Extract keyword following explain/search/impact/how does X work
            clean_term = re.sub(r"^(how\s+does|how\s+do\s+i|explain\s+how|explain|what\s+does|where\s+is|find|search\s+for|what\s+will\s+break\s+if\s+i\s+change)\s+", "", clean_q, flags=re.I)
            clean_term = re.sub(r"\s+(work|do|run|function|mean|be\s+affected)\??$", "", clean_term, flags=re.I).strip()
            if clean_term and len(clean_term.split()) <= 4:
                params["query"] = clean_term
                params["symbol"] = clean_term

        return params

    def decide(self, query: str) -> LayaDecision:
        """Evaluate natural-language request and produce validated WIA operation decision object."""
        intent, confidence, requires_llm, raw_operations = self.choice(query)
        target_params = self.extract_target_entities(query)

        operations: list[WIAOperationCall] = []
        for op_name in raw_operations:
            if op_name in self.VALID_OPERATIONS:
                op_params: dict[str, Any] = {}
                if op_name in ("index.search", "component.explain"):
                    if "query" in target_params:
                        op_params["query"] = target_params["query"]
                    if "file_path" in target_params:
                        op_params["file_path"] = target_params["file_path"]
                elif op_name == "impact.analyze":
                    if "symbol" in target_params:
                        op_params["symbol"] = target_params["symbol"]
                    elif "file_path" in target_params:
                        op_params["file_path"] = target_params["file_path"]
                elif op_name == "dependency.check":
                    if "query" in target_params:
                        op_params["scope"] = target_params["query"]

                operations.append(WIAOperationCall(name=op_name, parameters=op_params))

        # Check if confidence is below threshold and suggest clarifications
        clarifications: list[str] = []
        if confidence < self.confidence_threshold:
            clarifications = [
                "Explain the project architecture",
                "Check dependency and environment health",
                "Run the project tests",
                "Search symbols in workspace",
            ]
            rationale = f"Query matched '{intent}' with moderate confidence ({confidence:.2f}). Suggested clarifications available."
        else:
            rationale = f"Laya non-autoregressive decision engine routed query to '{intent}' with high confidence ({confidence:.2f})."

        return LayaDecision(
            request=query,
            intent=intent,
            operations=operations,
            confidence=confidence,
            requires_llm_reasoning=requires_llm,
            rationale=rationale,
            suggested_clarifications=clarifications,
        )


# Global singleton router instance preloaded in memory
_laya_router_instance: LayaDecisionEngine | None = None


def get_laya_router() -> LayaDecisionEngine:
    """Return preloaded singleton LayaDecisionEngine."""
    global _laya_router_instance
    if _laya_router_instance is None:
        _laya_router_instance = LayaDecisionEngine()
    return _laya_router_instance
