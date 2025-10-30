import logging
import os


def get_logger(name: str = __name__):
    """Return a configured logger. Level can be controlled with env var PRODUCT_AGG_LOG_LEVEL."""
    level = os.getenv("PRODUCT_AGG_LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(name)
    # Avoid adding multiple handlers in interactive sessions
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    try:
        logger.setLevel(level)
    except Exception:
        logger.setLevel("INFO")
    return logger
