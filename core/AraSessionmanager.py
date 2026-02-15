from core.AraService import AraService
from bus.JoLogger import get_logger
import uuid
from datetime import datetime

MAX_CHILDREN = 200
log = get_logger("SessionManager")


class AraSessionManager(AraService):

    def __init__(self, bus):
        self.bus = bus
        self.sessions = {}
        self._status = "stopped"
        self.bus.subscribe("child.connection.requested", self._handle_connection)

    def start(self):
        self._status = "running"
        log.info("Started.")

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _handle_connection(self, identity):
        device_name = identity["device_name"]
        log.debug("Connection request for '%s'", device_name)

        if len(self.sessions) >= MAX_CHILDREN:
            log.warning("Rejected '%s': max capacity (%d)", device_name, MAX_CHILDREN)
            self.bus.publish("session.rejected", {
                "device_name": device_name,
                "reason": "max_capacity_reached"
            })
            return

        if device_name in self.sessions:
            log.warning("Rejected '%s': duplicate device", device_name)
            self.bus.publish("session.rejected", {
                "device_name": device_name,
                "reason": "duplicate_device"
            })
            return

        session_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sessions[device_name] = {
            "session_id": session_id,
            "created_at": now,
            "last_seen": now
        }

        self.bus.publish("session.created", {
            "device_name": device_name,
            "session_id": session_id,
            "device_type": identity["device_type"],
            "created_at": now
        })
        log.info("Session created for '%s' (%d/%d)", device_name, len(self.sessions), MAX_CHILDREN)
