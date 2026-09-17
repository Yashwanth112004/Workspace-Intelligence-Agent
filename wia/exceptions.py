"""WIA exception hierarchy.

Provides clean custom exceptions for WIA operations.
"""

class WIAError(Exception):
    """Base exception for all WIA domain errors."""
    pass


class WorkspaceValidationError(WIAError):
    """Raised when a workspace directory fails validation."""
    pass


class IndexNotFoundError(WIAError):
    """Raised when attempting to access an index that does not exist."""
    pass


class IncompatibleIndexError(WIAError):
    """Raised when loading an index version incompatible with the current software."""
    pass


class StorageError(WIAError):
    """Raised when reading or writing workspace state/index files fails."""
    pass
