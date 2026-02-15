import time
from bus.JoLogger import get_logger

log = get_logger("RetryManager")


class AraRetryManager:
    """
    Phase 8 — Retry with exponential backoff.
    Wraps any callable and retries on failure.

    Usage:
        retry = AraRetryManager(max_retries=3, base_delay=1.0)
        result = retry.execute(some_function, arg1, arg2)
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 16.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def execute(self, func, *args, **kwargs):
        """
        Try func up to max_retries times with exponential backoff.
        Returns result on success, raises last exception on exhaustion.
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    log.warning("Attempt %d/%d failed: %s. Retry in %.1fs.",
                                attempt + 1, self.max_retries + 1, e, delay)
                    time.sleep(delay)
                else:
                    log.error("All %d attempts failed. Last error: %s",
                              self.max_retries + 1, e)

        raise last_error

    def execute_safe(self, func, *args, default=None, **kwargs):
        """Same as execute but returns default instead of raising."""
        try:
            return self.execute(func, *args, **kwargs)
        except Exception:
            return default
