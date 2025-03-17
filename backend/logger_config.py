import logging
import sys
from typing import Optional
from colorama import init, Fore, Style

# Initialize colorama for Windows support
init()


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""

    LEVEL_COLORS = {logging.DEBUG: Fore.CYAN, logging.INFO: Fore.GREEN, logging.WARNING: Fore.YELLOW, logging.ERROR: Fore.RED, logging.CRITICAL: Fore.RED + Style.BRIGHT}

    def format(self, record):
        # Get the original formatted message
        message = super().format(record)
        # Add color based on log level
        color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        return f"{color}{message}{Style.RESET_ALL}"


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with consistent configuration and colored output.

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

        # Create colored formatter
        formatter = ColoredFormatter("[%(asctime)s] %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        # Add formatter to handler
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    # Set level (default to INFO if not specified)
    logger.setLevel(level or logging.INFO)

    return logger


# Example usage:
if __name__ == "__main__":
    logger = setup_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
