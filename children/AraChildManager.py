from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("ChildManager")


class AraChildManager(AraService):

    def __init__(self, bus):
        self.bus = bus
        self.children = {}
        self._status = "stopped"
        self.bus.subscribe("session.created", self._add_child)
        self.bus.subscribe("session.rejected", self._remove_child)

    def start(self):
        self._status = "running"
        log.info("Started.")

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _add_child(self, session):
        device_name = session["device_name"]
        self.children[device_name] = {
            "device_type": session["device_type"],
            "session_id": session["session_id"],
            "connected_at": session["created_at"]
        }
        log.info("Registered: %s", device_name)

    def _remove_child(self, info):
        device_name = info.get("device_name")
        if device_name and device_name in self.children:
            del self.children[device_name]
            log.info("Removed: %s", device_name)

    def get_all(self):
        return self.children
