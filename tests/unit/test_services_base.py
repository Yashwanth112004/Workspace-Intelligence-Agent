"""Unit tests for BaseService and ServiceResult container."""

from wia.services.base import ServiceResult
from wia.exceptions import WorkspaceValidationError


def test_service_result_success():
    """Verify construction of successful ServiceResult objects."""
    res = ServiceResult.ok("Operation completed", data={"files": 42})
    assert res.success is True
    assert res.message == "Operation completed"
    assert res.data == {"files": 42}
    assert res.error is None


def test_service_result_failure():
    """Verify construction of failed ServiceResult objects."""
    err = WorkspaceValidationError("Path not found")
    res = ServiceResult.fail("Validation failed", error=err)
    assert res.success is False
    assert res.message == "Validation failed"
    assert res.data is None
    assert res.error == err
