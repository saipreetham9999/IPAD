import threading
import time
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("Watchdog")

WATCHDOG_INTERVAL = 60  # seconds between watchdog checks
STUCK_THRESHOLD = 120   # if no bus activity for this long, something is wrong


class AraWatchdog(AraService):
    """
    Phase 8 — Watchdog timer for the Brain.
    Monitors that the system is alive by tracking JoBus activity.
    If no events flow for STUCK_THRESHOLD seconds, fires a warning.
    """

    def __init__(self, bus, telegram_bot=None):
        self.bus = bus
        self.telegram_bot = telegram_bot
        self._status = "stopped"
        self._running = False
        self._thread = None
        self._last_activity = time.time()
        self._lock = threading.Lock()

    def start(self):
        if self._status == "running":
            return
        self._running = True
        self._status = "running"
        self._last_activity = time.time()

        # Tap into bus to track activity
        self.bus.subscribe("session.created", self._on_activity)
        self.bus.subscribe("child.disconnected", self._on_activity)
        self.bus.subscribe("alert.triggered", self._on_activity)
        self.bus.subscribe("child.report.received", self._on_activity)
        self.bus.subscribe("telegram.command", self._on_activity)

        self._thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._thread.start()
        log.info("Started. Check interval: %ds, stuck threshold: %ds.",
                 WATCHDOG_INTERVAL, STUCK_THRESHOLD)

    def stop(self):
        self._running = False
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _on_activity(self, _payload):
        with self._lock:
            self._last_activity = time.time()

    def _watchdog_loop(self):
        while self._running:
            time.sleep(WATCHDOG_INTERVAL)

            with self._lock:
                idle = time.time() - self._last_activity

            if idle > STUCK_THRESHOLD:
                log.warning("No bus activity for %.0fs — system may be stuck.", idle)
                self.bus.publish("alert.triggered", {
                    "source": "Watchdog",
                    "message": f"No activity for {int(idle)}s — possible system stall.",
                })
            else:
                log.debug("System alive. Last activity %.0fs ago.", idle)

    def seconds_since_activity(self) -> float:
        with self._lock:
            return time.time() - self._last_activity
