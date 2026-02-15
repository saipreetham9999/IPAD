import threading
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("MessageRouter")


class MiniMessageRouter(AraService):
    """
    Per-child event queue.
    Brain puts messages in -> child polls /api/events -> gets them -> queue clears.
    """

    def __init__(self, bus):
        self.bus = bus
        self._status = "stopped"
        self._lock = threading.Lock()
        self._queues = {}

    def start(self):
        if self._status == "running":
            return
        self._status = "running"
        log.info("Started.")
        self.bus.subscribe("session.created", self._on_child_connected)
        self.bus.subscribe("child.disconnected", self._on_child_disconnected)
        self.bus.subscribe("alert.triggered", self._on_alert)

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _on_child_connected(self, data: dict):
        device_name = data.get("device_name")
        if not device_name:
            return
        with self._lock:
            if device_name not in self._queues:
                self._queues[device_name] = []
        log.info("Queue created for '%s'", device_name)
        self._broadcast({
            "type": "child.connected",
            "device_name": device_name,
            "device_type": data.get("device_type", "unknown")
        }, exclude=device_name)

    def _on_child_disconnected(self, data: dict):
        device_name = data.get("device_name")
        if not device_name:
            return
        with self._lock:
            if device_name in self._queues:
                del self._queues[device_name]
        log.info("Queue removed for '%s'", device_name)
        self._broadcast({
            "type": "child.disconnected",
            "device_name": device_name,
            "reason": data.get("reason", "unknown")
        })

    def _on_alert(self, data: dict):
        log.info("Broadcasting alert to all children")
        self._broadcast({
            "type": "alert",
            "payload": data
        })

    def push_to(self, device_name: str, event: dict):
        with self._lock:
            if device_name not in self._queues:
                self._queues[device_name] = []
            self._queues[device_name].append(event)

    def _broadcast(self, event: dict, exclude: str = None):
        with self._lock:
            for name in self._queues:
                if name != exclude:
                    self._queues[name].append(event)

    def pop_events(self, device_name: str) -> list:
        with self._lock:
            if device_name not in self._queues:
                return []
            events = list(self._queues[device_name])
            self._queues[device_name] = []
            return events
