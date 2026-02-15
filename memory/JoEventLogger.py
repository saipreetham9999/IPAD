import os
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("EventLogger")

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
EVENT_FILE = "events.log"
MAX_BYTES = 2 * 1024 * 1024  # 2 MB per file
BACKUP_COUNT = 2              # 3 files total = ~6 MB for events

# Events to track
TRACKED_EVENTS = [
    "child.connection.requested",
    "session.created",
    "session.rejected",
    "child.disconnected",
    "alert.triggered",
    "child.report.received",
    "telegram.command",
]


class JoEventLogger(AraService):
    """
    Phase 6 — logs all JoBus events to a rotating file.
    Lightweight: one line per event, rotating files, bounded storage.
    """

    def __init__(self, bus):
        self.bus = bus
        self._status = "stopped"
        self._lock = threading.Lock()
        self._file_handler = None

    def start(self):
        if self._status == "running":
            return
        self._status = "running"

        # Set up rotating event log file
        os.makedirs(LOG_DIR, exist_ok=True)
        self._file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, EVENT_FILE),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
        )

        # Subscribe to all tracked events
        for event_name in TRACKED_EVENTS:
            self.bus.subscribe(event_name, self._make_handler(event_name))

        log.info("Started. Tracking %d event types.", len(TRACKED_EVENTS))

    def stop(self):
        self._status = "stopped"
        if self._file_handler:
            self._file_handler.close()
            self._file_handler = None
        log.info("Stopped.")

    def status(self):
        return self._status

    def _make_handler(self, event_name):
        """Returns a closure that logs events with the event name."""
        def handler(payload):
            self._log_event(event_name, payload)
        handler.__name__ = f"_log_{event_name}"
        return handler

    def _log_event(self, event_name: str, payload):
        """Write one line per event to the rotating log."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Keep payload compact — one line
        summary = self._summarize(payload)
        line = f"[{ts}] {event_name} | {summary}\n"

        with self._lock:
            if self._file_handler:
                try:
                    self._file_handler.stream.write(line)
                    self._file_handler.stream.flush()
                    # Check if rotation needed
                    if self._file_handler.stream.tell() >= MAX_BYTES:
                        self._file_handler.doRollover()
                except Exception as e:
                    log.error("Failed to write event: %s", e)

    def _summarize(self, payload) -> str:
        """Convert payload to a compact single-line string."""
        if payload is None:
            return "-"
        if isinstance(payload, str):
            return payload[:120]
        if isinstance(payload, dict):
            parts = []
            for k, v in payload.items():
                val = str(v)[:40]
                parts.append(f"{k}={val}")
            return ", ".join(parts)[:200]
        return str(payload)[:120]
