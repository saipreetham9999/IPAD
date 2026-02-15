import time
import threading
from bus.JoLogger import get_logger

log = get_logger("CircuitBreaker")

# States
CLOSED = "closed"      # Normal — calls go through
OPEN = "open"          # Tripped — all calls rejected
HALF_OPEN = "half_open"  # Testing — one call allowed through


class JoCircuitBreaker:
    """
    Phase 8 — Circuit breaker pattern.
    Wraps any callable. If it fails too many times, the breaker opens
    and rejects calls for a cooldown period before allowing a retry.

    Usage:
        breaker = JoCircuitBreaker("telegram_send", max_failures=3)
        result = breaker.call(some_function, arg1, arg2)
    """

    def __init__(self, name: str, max_failures: int = 3, cooldown: int = 30):
        self.name = name
        self.max_failures = max_failures
        self.cooldown = cooldown  # seconds
        self._state = CLOSED
        self._failure_count = 0
        self._last_failure_time = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == OPEN:
                if time.time() - self._last_failure_time >= self.cooldown:
                    self._state = HALF_OPEN
                    log.info("[%s] Moved to HALF_OPEN — allowing test call.", self.name)
            return self._state

    def call(self, func, *args, **kwargs):
        """
        Execute func through the circuit breaker.
        Returns result on success, None on open circuit.
        """
        current = self.state

        if current == OPEN:
            log.debug("[%s] OPEN — call rejected.", self.name)
            return None

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            log.warning("[%s] Call failed: %s", self.name, e)
            return None

    def _on_success(self):
        with self._lock:
            self._failure_count = 0
            if self._state == HALF_OPEN:
                log.info("[%s] Test call succeeded — closing circuit.", self.name)
            self._state = CLOSED

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.max_failures:
                self._state = OPEN
                log.warning("[%s] Circuit OPEN after %d failures. Cooldown: %ds.",
                            self.name, self._failure_count, self.cooldown)

    def reset(self):
        with self._lock:
            self._state = CLOSED
            self._failure_count = 0
            log.info("[%s] Manually reset.", self.name)
