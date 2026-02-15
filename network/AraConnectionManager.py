import threading
import time
from core.AraService import AraService


class AraConnectionManager(AraService):

    def __init__(self, bus):
        self.bus = bus
        self._status = "stopped"
        self._lock = threading.Lock()
        # active_children = { device_name: { identity + last_seen } }
        self.active_children = {}
        self._cleanup_thread = None
        self._running = False
        self.HEARTBEAT_TIMEOUT = 15  # seconds before child marked lost

    # ── called by Flask route POST /api/connect ──────────────────────
    def handle_connect(self, identity: dict) -> dict:
        device_name = identity.get("device_name")
        device_type = identity.get("device_type")

        if not device_name or not device_type:
            return {"status": "rejected", "reason": "device_name and device_type required"}

        with self._lock:
            self.active_children[device_name] = {
                "device_name": device_name,
                "device_type": device_type,
                "capabilities": identity.get("capabilities", []),
                "connected_at": time.time(),
                "last_seen": time.time(),
            }

        print(f"[AraConnectionManager] '{device_name}' connected. Total: {len(self.active_children)}")
        self.bus.publish("child.connection.requested", identity)

        return {"status": "connected", "device": device_name}

    # ── called by Flask route POST /api/heartbeat ─────────────────────
    def handle_heartbeat(self, device_name: str) -> dict:
        with self._lock:
            if device_name in self.active_children:
                self.active_children[device_name]["last_seen"] = time.time()
                return {"status": "ok"}
            else:
                return {"status": "unknown", "reason": "not registered, reconnect"}

    # ── called by Flask route POST /api/disconnect ────────────────────
    def handle_disconnect(self, device_name: str):
        with self._lock:
            if device_name in self.active_children:
                del self.active_children[device_name]
                print(f"[AraConnectionManager] '{device_name}' disconnected.")
        self.bus.publish("child.disconnected", {"device_name": device_name, "reason": "client_request"})

    # ── background cleanup — removes silent children ──────────────────
    def _cleanup_loop(self):
        while self._running:
            time.sleep(5)
            now = time.time()
            lost = []

            with self._lock:
                for name, child in self.active_children.items():
                    if now - child["last_seen"] > self.HEARTBEAT_TIMEOUT:
                        lost.append(name)

                for name in lost:
                    del self.active_children[name]
                    print(f"[AraConnectionManager] '{name}' timed out — removed.")

            for name in lost:
                self.bus.publish("child.disconnected", {"device_name": name, "reason": "heartbeat_timeout"})

    def get_all(self) -> dict:
        with self._lock:
            return dict(self.active_children)

    # ── AraService interface ──────────────────────────────────────────
    def start(self):
        if self._status == "running":
            return
        self._running = True
        self._status = "running"
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        print("[AraConnectionManager] Started. Waiting for HTTP connections on /api/connect")

    def stop(self):
        self._running = False
        self._status = "stopped"
        print("[AraConnectionManager] Stopped.")

    def status(self):
        return self._status