import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with consistent configuration.

    Args:
        name: Name of the logger (usually __name__ of the module)
        level: Optional logging level (defaults to INFO if not specified)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Only add handler if the logger doesn't already have handlers
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)

        # Create formatter
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        # Add formatter to handler
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    # Set level (default to INFO if not specified)
    logger.setLevel(level or logging.INFO)

    return logger
