from core.AraService import AraService
import uuid
from datetime import datetime

MAX_CHILDREN = 20

class AraSessionManager(AraService):

    def __init__(self, bus):
        self.bus = bus
        self.sessions = {}
        self._status = "stopped"
        self.bus.subscribe("child.connection.requested", self._handle_connection)

    def start(self):
        self._status = "running"
        print("[SessionManager] Started.") # Added diagnostic print

    def stop(self):
        self._status = "stopped"
        print("[SessionManager] Stopped.") # Added diagnostic print

    def status(self):
        return self._status

    def _handle_connection(self, identity):
        device_name = identity["device_name"]
        print(f"[SessionManager] Received connection request for '{device_name}'.") # Added diagnostic print

        # Check max children
        if len(self.sessions) >= MAX_CHILDREN:
            print(f"[SessionManager] Rejected connection for '{device_name}': Max capacity ({MAX_CHILDREN}) reached.") # Added diagnostic print
            self.bus.publish("session.rejected", {
                "device_name": device_name,
                "reason": "max_capacity_reached"
            })
            return

        # Check duplicates
        if device_name in self.sessions:
            print(f"[SessionManager] Rejected connection for '{device_name}': Duplicate device.") # Added diagnostic print
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
        print(f"[SessionManager] Created session for '{device_name}' (ID: {session_id}). Total active: {len(self.sessions)}/{MAX_CHILDREN}") # Added diagnostic print
