from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.AraService import AraService
import threading
import uvicorn


# Identity schema (validation layer)
class IdentityPayload(BaseModel):
    device_name: str
    device_type: str
    capabilities: list[str] = []
    token: str = None # Added optional token


class AraConnectionManager(AraService):

    def __init__(self, bus, host="0.0.0.0", port=8000):
        self.bus = bus
        self.host = host
        self.port = port
        self._status = "stopped"

        self.app = FastAPI(title="BRAIN Connection Server")

        self._register_routes()

    def _register_routes(self):

        @self.app.post("/connect")
        async def connect(identity: IdentityPayload):
            print(f"[AraConnectionManager] Received /connect request from {identity.device_name}")

            # Basic validation (structural)
            if not identity.device_name or not identity.device_type:
                raise HTTPException(status_code=400, detail="Invalid identity: device_name and device_type are required")

            # Optional token validation (placeholder for now)
            # if identity.token != "your-shared-secret":
            #     raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")

            identity_dict = identity.model_dump()

            # Publish event to system - changed event name
            self.bus.publish("child.connection.requested", identity_dict)
            print(f"[AraConnectionManager] Published 'child.connection.requested' for {identity.device_name}")

            # Return immediate response
            return {"status": "request received"}

        @self.app.get("/health")
        async def health():
            return {"status": "ok"}

    def start(self):
        if self._status == "running":
            return

        self._status = "running"
        print(f"[AraConnectionManager.start] Attempting to start FastAPI server on {self.host}:{self.port}...")

        threading.Thread(
            target=uvicorn.run,
            args=(self.app,),
            kwargs={
                "host": self.host,
                "port": self.port,
                "log_level": "info"
            },
            daemon=True
        ).start()
        print("[AraConnectionManager.start] FastAPI server thread initiated.")

        print(f"[ConnectionManager] Running on {self.host}:{self.port}")

    def stop(self):
        self._status = "stopped"

    def status(self):
        return self._status
