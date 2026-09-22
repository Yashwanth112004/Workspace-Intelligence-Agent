"""Unit tests for Laya Decision Engine and Router."""

from wia.core.laya_router import LayaDecisionEngine, get_laya_router


def test_laya_router_initialization():
    engine = get_laya_router()
    assert isinstance(engine, LayaDecisionEngine)
    assert len(engine.intent_patterns) > 0


def test_laya_router_project_run():
    engine = get_laya_router()
    decision = engine.decide("How do I run this project?")
    assert decision.intent == "project_run"
    assert decision.confidence >= 0.90
    assert not decision.requires_llm_reasoning
    assert any(op.name == "project.run" for op in decision.operations)


def test_laya_router_project_test():
    engine = get_laya_router()
    decision = engine.decide("Run the tests")
    assert decision.intent == "project_test"
    assert decision.confidence >= 0.90
    assert not decision.requires_llm_reasoning
    assert any(op.name == "project.test" for op in decision.operations)


def test_laya_router_dependency_check():
    engine = get_laya_router()
    decision = engine.decide("Check dependencies and missing packages")
    assert decision.intent == "dependency_check"
    assert any(op.name in ("dependency.check", "dependency.list") for op in decision.operations)


def test_laya_router_architecture_overview():
    engine = get_laya_router()
    decision = engine.decide("Explain the project architecture and subsystem boundaries")
    assert decision.intent == "architecture_overview"
    assert decision.confidence >= 0.90
    assert decision.requires_llm_reasoning
    assert any(op.name == "architecture.analyze" for op in decision.operations)


def test_laya_router_impact_analysis():
    engine = get_laya_router()
    decision = engine.decide("What will break if I change auth.py?")
    assert decision.intent == "impact_analysis"
    assert any(op.name == "impact.analyze" for op in decision.operations)
    assert any("auth.py" in str(op.parameters) for op in decision.operations)


def test_laya_router_choice_score_noul_primitives():
    engine = get_laya_router()

    # choice
    intent, conf, req_llm, ops = engine.choice("Run tests")
    assert intent == "project_test"
    assert conf > 0.8

    # score
    score_val = engine.score("Run tests", "project_test")
    assert 0.0 <= score_val <= 1.0

    # noul
    is_match, prob = engine.noul("Run tests", "project_test")
    assert is_match is True
    assert prob > 0.8
