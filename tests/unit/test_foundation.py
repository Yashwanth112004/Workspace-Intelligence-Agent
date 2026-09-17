"""Unit tests for Step 1 package foundation."""

import wia
from wia.constants import WIA_DIR_NAME, CURRENT_INDEX_SCHEMA_VERSION
from wia.exceptions import WIAError, WorkspaceValidationError


def test_package_version():
    """Verify single source of truth version definition."""
    assert hasattr(wia, "__version__")
    assert isinstance(wia.__version__, str)
    assert wia.__version__ == "0.1.0"


def test_constants():
    """Verify core workspace constants."""
    assert WIA_DIR_NAME == ".wia"
    assert CURRENT_INDEX_SCHEMA_VERSION == "1.0"


def test_exception_hierarchy():
    """Verify custom WIA exception inheritance structure."""
    err = WorkspaceValidationError("Invalid path")
    assert isinstance(err, WIAError)
    assert isinstance(err, Exception)
    assert str(err) == "Invalid path"
