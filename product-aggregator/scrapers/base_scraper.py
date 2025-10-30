"""Common scraper helpers: driver creation and simple retry helper.

This keeps the individual scraper modules small and provides consistent
error messages, retries and headless configuration.
"""
import time
from typing import Callable

import undetected_chromedriver as uc
from selenium.common.exceptions import SessionNotCreatedException

from utils.logger import get_logger

logger = get_logger(__name__)


def make_driver(headless: bool = True):
    """Create and return an undetected_chromedriver.Chrome instance.

    Raises SessionNotCreatedException with a helpful message when Chrome/driver
    can't start.
    """
    opts = uc.ChromeOptions()
    if headless:
        # newer headless flag
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    try:
        return uc.Chrome(options=opts)
    except SessionNotCreatedException as e:
        raise SessionNotCreatedException(
            f"Could not start Chrome. Ensure Chrome is installed and compatible with undetected_chromedriver. Original: {e}"
        )


def retry_call(func: Callable, retries: int = 2, delay: float = 1.0, *args, **kwargs):
    """Simple retry wrapper with exponential backoff.

    Returns the return value of func or raises the last exception after retries.
    """
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            logger.warning("Attempt %d/%d failed: %s", attempt, retries, e)
            time.sleep(delay * attempt)
    # re-raise the last exception
    raise last_exc
