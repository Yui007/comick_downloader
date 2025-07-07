import logging
from rich.logging import RichHandler

def setup_logger():
    """Sets up a logger with RichHandler."""
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger("rich")

log = setup_logger()
