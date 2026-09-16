from enum import Enum
from typing import Dict, Any, Optional

class QueryIntent(str, Enum):
    ARCHITECTURE = "ARCHITECTURE"
    CODE_FLOW = "CODE_FLOW"
    DEPENDENCY_IMPACT = "DEPENDENCY_IMPACT"
    SYMBOL_LOOKUP = "SYMBOL_LOOKUP"
    ONBOARDING = "ONBOARDING"
    HEALTH_AUDIT = "HEALTH_AUDIT"
    GENERAL_QA = "GENERAL_QA"

class QueryPlanner:
    """Classifies user question intent to route optimal hybrid retrieval strategies."""

    @staticmethod
    def plan_query(user_query: str) -> Dict[str, Any]:
        q_lower = user_query.lower()

        if any(w in q_lower for w in ["architecture", "overview", "subsystem", "design", "high level"]):
            return {
                "intent": QueryIntent.ARCHITECTURE.value,
                "needs_graph": True,
                "needs_summaries": True,
                "needs_symbols": False
            }

        if any(w in q_lower for w in ["flow", "trace", "call", "what happens when", "execution", "lifecycle"]):
            return {
                "intent": QueryIntent.CODE_FLOW.value,
                "needs_graph": True,
                "needs_symbols": True,
                "needs_summaries": False
            }

        if any(w in q_lower for w in ["impact", "affect", "modify", "change", "depend on", "who uses"]):
            return {
                "intent": QueryIntent.DEPENDENCY_IMPACT.value,
                "needs_graph": True,
                "needs_symbols": True,
                "needs_summaries": False
            }

        if any(w in q_lower for w in ["onboard", "new developer", "getting started", "where do i start"]):
            return {
                "intent": QueryIntent.ONBOARDING.value,
                "needs_graph": True,
                "needs_summaries": True,
                "needs_symbols": False
            }

        if any(w in q_lower for w in ["health", "complexity", "circular", "dead code", "smell", "audit"]):
            return {
                "intent": QueryIntent.HEALTH_AUDIT.value,
                "needs_graph": True,
                "needs_symbols": True,
                "needs_summaries": False
            }

        if any(w in q_lower for w in ["function", "class", "method", "interface", "signature", "defined"]):
            return {
                "intent": QueryIntent.SYMBOL_LOOKUP.value,
                "needs_graph": True,
                "needs_symbols": True,
                "needs_summaries": False
            }

        return {
            "intent": QueryIntent.GENERAL_QA.value,
            "needs_graph": True,
            "needs_summaries": True,
            "needs_symbols": True
        }
