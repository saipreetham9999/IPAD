import threading
import time
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("ReconnectManager")

RECONNECT_WINDOW = 60  # seconds a device has to reconnect before being forgotten
CLEANUP_INTERVAL = 15  # seconds between cleanup sweeps


class AraReconnectManager(AraService):
    """
    Phase 7 — tracks recently disconnected devices and allows graceful reconnection.
    If a device reconnects within RECONNECT_WINDOW, it gets its old session back.
    """

    def __init__(self, bus):
        self.bus = bus
        self._status = "stopped"
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        # { device_name: { disconnected_at, session_data } }
        self._pending = {}

    def start(self):
        if self._status == "running":
            return
        self._running = True
        self._status = "running"
        self.bus.subscribe("child.disconnected", self._on_disconnect)
        self.bus.subscribe("child.connection.requested", self._on_reconnect_attempt)
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()
        log.info("Started. Reconnect window: %ds.", RECONNECT_WINDOW)

    def stop(self):
        self._running = False
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _on_disconnect(self, data: dict):
        device_name = data.get("device_name")
        if not device_name:
            return
        with self._lock:
            self._pending[device_name] = {
                "disconnected_at": time.time(),
                "reason": data.get("reason", "unknown"),
            }
        log.debug("'%s' added to reconnect pool.", device_name)

    def _on_reconnect_attempt(self, data: dict):
        device_name = data.get("device_name")
        if not device_name:
            return
        with self._lock:
            if device_name in self._pending:
                elapsed = time.time() - self._pending[device_name]["disconnected_at"]
                del self._pending[device_name]
                log.info("'%s' reconnected after %.0fs.", device_name, elapsed)

    def _cleanup_loop(self):
        while self._running:
            time.sleep(CLEANUP_INTERVAL)
            now = time.time()
            expired = []
            with self._lock:
                for name, info in self._pending.items():
                    if now - info["disconnected_at"] > RECONNECT_WINDOW:
                        expired.append(name)
                for name in expired:
                    del self._pending[name]
            if expired:
                log.debug("Expired %d from reconnect pool: %s", len(expired), expired)

    def is_pending(self, device_name: str) -> bool:
        with self._lock:
            return device_name in self._pending
