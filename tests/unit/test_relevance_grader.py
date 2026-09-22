"""Unit tests for ResponseRelevanceGrader and LLM response structure validation."""

from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.llm.relevance import ResponseRelevanceGrader


def _create_sample_index() -> WorkspaceIndex:
    files = {
        "wia/core/retrieval.py": FileRecord(
            relative_path="wia/core/retrieval.py",
            file_size=1024,
            modified_time=1700000000.0,
            extension=".py",
            language="Python",
            file_type="Source Code",
            indexing_status=IndexingStatus.INDEXED,
        ),
        "wia/services/indexing_service.py": FileRecord(
            relative_path="wia/services/indexing_service.py",
            file_size=2048,
            modified_time=1700000000.0,
            extension=".py",
            language="Python",
            file_type="Source Code",
            indexing_status=IndexingStatus.INDEXED,
        ),
    }
    return WorkspaceIndex(workspace_path="/test", files=files)


def test_relevance_grader_high_relevance_grounded():
    index = _create_sample_index()
    prompt = "How does indexing work in indexing_service.py?"
    response = (
        "### Executive Summary / Direct Answer\n"
        "Indexing is orchestrated by `wia/services/indexing_service.py` using parallel workers.\n\n"
        "### Architecture & System Context\n"
        "The indexing service partitions files into batches and extracts AST symbols.\n\n"
        "### Key Symbols & Implementation\n"
        "- `IndexingService.index_workspace`\n\n"
        "### Evidence & Grounded Citations\n"
        "- `wia/services/indexing_service.py:120-150`"
    )

    assessment = ResponseRelevanceGrader.evaluate(prompt, response, index=index)
    assert assessment.is_relevant is True
    assert assessment.relevance_score >= 0.75
    assert assessment.grounding_score >= 0.80
    assert "wia/services/indexing_service.py:120-150" in assessment.verified_citations
    assert "Relevance & Grounding" in assessment.summary_badge()


def test_relevance_grader_detects_unverified_citations():
    index = _create_sample_index()
    prompt = "Where is the database stored?"
    response = (
        "### Executive Summary\n"
        "Data is stored in `nonexistent/database.sqlite`.\n\n"
        "### Evidence\n"
        "- `nonexistent/database.sqlite`"
    )

    assessment = ResponseRelevanceGrader.evaluate(prompt, response, index=index)
    assert len(assessment.unverified_citations) >= 1
    assert len(assessment.hallucination_warnings) >= 1
    assert "nonexistent/database.sqlite" in assessment.unverified_citations


def test_relevance_grader_empty_response():
    assessment = ResponseRelevanceGrader.evaluate("test", "")
    assert assessment.is_relevant is False
    assert assessment.relevance_score == 0.0
