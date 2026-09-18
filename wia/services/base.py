"""Base application service abstractions and result containers."""

from dataclasses import dataclass
from typing import Generic, TypeVar, Any

T = TypeVar("T")


@dataclass
class ServiceResult(Generic[T]):
    """Standard container for service execution results.

    Encapsulates success status, message, returned data payload,
    and optional domain exception instance.
    """

    success: bool
    message: str
    data: T | None = None
    error: Exception | None = None

    @classmethod
    def ok(cls, message: str, data: T | None = None) -> "ServiceResult[T]":
        """Construct a successful service execution result."""
        return cls(success=True, message=message, data=data, error=None)

    @classmethod
    def fail(cls, message: str, error: Exception | None = None) -> "ServiceResult[T]":
        """Construct a failed service execution result."""
        return cls(success=False, message=message, data=None, error=error)


class BaseService:
    """Base class for all WIA application orchestration services."""

    pass
