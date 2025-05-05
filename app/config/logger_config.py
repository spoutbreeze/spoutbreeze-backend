import logging
import sys


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Create and configure a logger.

    Args:
        name (str): The name of the logger. Defaults to the module name.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Create a custom logger
    logger = logging.getLogger(name)

    # Set the default logging level
    logger.setLevel(logging.DEBUG)

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Create formatters and add them to handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


logger = get_logger("SpoutBreeze")
