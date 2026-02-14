from core.AraService import AraService
from bus.JoBus import JoBus # Assuming JoBus is needed for subscription

class AraChildManager(AraService):

    def __init__(self, bus):
        self.bus = bus
        self.children = {}
        self._status = "stopped"
        self.bus.subscribe("session.created", self._add_child)
        # Note: session.rejected means a session was never created.
        # A child would only be in self.children if session.created was published.
        # So, _remove_child being called on session.rejected will likely try to remove a child that was never added.
        # This might need refinement later, perhaps subscribing to session.expired or child.disconnected.
        self.bus.subscribe("session.rejected", self._remove_child)

    def start(self):
        self._status = "running"
        print("[ChildManager] Started.") # Added diagnostic print

    def stop(self):
        self._status = "stopped"
        print("[ChildManager] Stopped.") # Added diagnostic print

    def status(self):
        return self._status

    def _add_child(self, session):
        device_name = session["device_name"]
        self.children[device_name] = {
            "device_type": session["device_type"],
            "session_id": session["session_id"],
            "connected_at": session["created_at"]
        }
        print(f"[ChildManager] Child registered: {device_name} (ID: {session['session_id']})") # Added diagnostic print

    def _remove_child(self, info):
        # This method is called on session.rejected.
        # As noted in __init__, this might be trying to remove a child that was never added.
        device_name = info.get("device_name")
        if device_name and device_name in self.children:
            del self.children[device_name]
            print(f"[ChildManager] Child '{device_name}' removed from registry.") # Added diagnostic print
        else:
            print(f"[ChildManager] Attempted to remove unknown child '{device_name}' on session.rejected.") # Added diagnostic print

    def get_all(self):
        return self.children
