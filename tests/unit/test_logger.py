"""Unit tests for setup_logger logging engine."""

import logging
from wia.utils.logger import setup_logger


def test_setup_logger_default():
    """Verify logger setup defaults to INFO level."""
    logger = setup_logger("test_logger", verbose=False)
    assert logger.level == logging.INFO


def test_setup_logger_verbose():
    """Verify logger setup sets DEBUG level when verbose=True."""
    logger = setup_logger("test_logger_verbose", verbose=True)
    assert logger.level == logging.DEBUG
