"""Structured logging configuration for WIA CLI."""

import logging
import sys


def setup_logger(name: str = "wia", verbose: bool = False) -> logging.Logger:
    """Configure and return structured Logger for WIA.

    When verbose is True, logging level is set to DEBUG.
    Otherwise, logging level defaults to INFO.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Avoid duplicate handlers on re-initialization
    if logger.handlers:
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG if verbose else logging.WARNING)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
