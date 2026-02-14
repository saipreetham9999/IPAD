import asyncio  # For asynchronous operations
import json  # To handle JSON messages over WebSocket
import threading  # To run the async server in a separate thread
import websockets  # The new WebSocket library

from core.AraService import AraService  # Assuming AraService is PascalCase


# Identity validation (simplified without Pydantic)
class IdentityPayload:
    def __init__(self, device_name: str, device_type: str, capabilities: list = None, token: str = None):
        self.device_name = device_name
        self.device_type = device_type
        self.capabilities = capabilities if capabilities is not None else []
        self.token = token

    def to_dict(self):
        return {
            "device_name": self.device_name,
            "device_type": self.device_type,
            "capabilities": self.capabilities,
            "token": self.token
        }


class AraConnectionManager(AraService):

    def __init__(self, bus, host="0.0.0.0", port=8000):
        self.bus = bus
        self.host = host
        self.port = port
        self._status = "stopped"
        self.active_connections: dict[
            str, websockets.WebSocketServerProtocol] = {}  # To store active WebSocket connections
        self._websocket_server = None  # To hold the WebSocket server instance
        self._loop = None  # To hold the asyncio event loop for the server thread

    async def _websocket_handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """
        Handles incoming WebSocket connections.
        """
        device_name = "unknown"  # Default for logging before identity is received
        try:
            print(f"[AraConnectionManager] Incoming WebSocket connection from {websocket.remote_address}.")

            # First message from client should be identity
            identity_json = await websocket.recv()
            identity_data = json.loads(identity_json)  # Parse JSON string

            # Manual validation of identity
            if not isinstance(identity_data, dict):
                await websocket.send(json.dumps({"status": "rejected", "reason": "Invalid JSON format for identity"}))
                raise websockets.exceptions.ConnectionClosedOK(code=1008, reason="Invalid identity format")

            device_name = identity_data.get("device_name")
            device_type = identity_data.get("device_type")
            capabilities = identity_data.get("capabilities", [])
            token = identity_data.get("token")

            # Basic validation (structural)
            if not device_name or not device_type:
                await websocket.send(json.dumps(
                    {"status": "rejected", "reason": "Invalid identity: device_name and device_type are required"}))
                raise websockets.exceptions.ConnectionClosedOK(code=1008, reason="Invalid identity")

            # Optional token validation (placeholder for now)
            # if token != "your-shared-secret":
            #     await websocket.send(json.dumps({"status": "rejected", "reason": "Unauthorized: Invalid token"}))
            #     raise websockets.exceptions.ConnectionClosedOK(code=1008, reason="Unauthorized")

            identity_payload = IdentityPayload(device_name, device_type, capabilities, token)
            identity_dict = identity_payload.to_dict()

            print(f"[AraConnectionManager] Received identity from '{device_name}' via WebSocket.")

            # Store the active connection
            self.active_connections[device_name] = websocket
            print(
                f"[AraConnectionManager] Stored WebSocket for '{device_name}'. Total active: {len(self.active_connections)}")

            # Publish event to system
            self.bus.publish("child.connection.requested", identity_dict)
            print(f"[AraConnectionManager] Published 'child.connection.requested' for {device_name}")

            # Send initial success response over WebSocket
            await websocket.send(json.dumps({"status": "connected", "device": device_name}))

            # Keep the connection alive, listening for further messages
            while True:
                # This loop can be used to receive commands/data from the client
                # or just keep the connection open.
                message = await websocket.recv()
                print(f"[AraConnectionManager] Received data from '{device_name}': {message}")
                # Example: echo back
                # await websocket.send(f"Echo: {message}")

        except websockets.exceptions.ConnectionClosedOK:
            print(f"[AraConnectionManager] WebSocket connection closed gracefully for '{device_name}'.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(
                f"[AraConnectionManager] WebSocket connection closed with error for '{device_name}' (Code: {e.code}, Reason: {e.reason}).")
        except json.JSONDecodeError:
            print(f"[AraConnectionManager] Invalid JSON received from client '{device_name}'.")
            # Attempt to send rejection if connection is still open
            try:
                await websocket.send(json.dumps({"status": "rejected", "reason": "Invalid JSON format"}))
            except websockets.exceptions.ConnectionClosed:
                pass  # Already closed
        except Exception as e:
            print(f"[AraConnectionManager] Error in WebSocket connection for '{device_name}': {e}")
        finally:
            if device_name in self.active_connections:
                del self.active_connections[device_name]
                print(
                    f"[AraConnectionManager] Removed WebSocket for '{device_name}'. Total active: {len(self.active_connections)}")
            # Optionally publish a child.disconnected event
            self.bus.publish("child.disconnected", {"device_name": device_name, "reason": "websocket_closed"})

    async def _serve_websocket_forever(self):
        """Coroutine to start and keep the WebSocket server running."""
        try:
            self._websocket_server = await websockets.serve(self._websocket_handler, self.host, self.port)
            print(f"[ConnectionManager] WebSocket server running on ws://{self.host}:{self.port}")
            # This will keep the server running until it's explicitly stopped or the loop is closed
            await asyncio.Future()  # Await an unresolved Future to keep the task alive
        except Exception as e:
            print(f"[ConnectionManager] Error starting WebSocket server: {e}")
            # Propagate error or handle it

    def _run_websocket_server(self):
        """
        Runs the asyncio event loop for the WebSocket server in a separate thread.
        """
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            # Run the coroutine that starts the server and keeps it alive
            self._loop.run_until_complete(self._serve_websocket_forever())
        except asyncio.CancelledError:
            print("[ConnectionManager] WebSocket server loop cancelled.")
        except Exception as e:
            print(f"[ConnectionManager] Unhandled exception in WebSocket server thread: {e}")
        finally:
            self._loop.close()
            print("[ConnectionManager] WebSocket server loop closed.")

    def start(self):
        if self._status == "running":
            return

        self._status = "running"
        print(f"[AraConnectionManager.start] Attempting to start WebSocket server on ws://{self.host}:{self.port}...")

        # Run the asyncio event loop in a separate daemon thread
        threading.Thread(
            target=self._run_websocket_server,
            daemon=True
        ).start()
        print("[AraConnectionManager.start] WebSocket server thread initiated.")

    def stop(self):
        if self._status == "running":
            self._status = "stopped"
            print("[ConnectionManager] Stopping WebSocket server...")
            if self._websocket_server:
                self._websocket_server.close()
                # Schedule the close operation to run in the server's loop
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(self._websocket_server.wait_closed(), self._loop)
                    # Stop the loop itself
                    self._loop.call_soon_threadsafe(self._loop.stop)
            print("[ConnectionManager] WebSocket server stopped.")

    def status(self):
        return self._status

    # New method to send data to a specific connected device
    async def send_to_device(self, device_name: str, message: dict):
        if device_name in self.active_connections:
            websocket = self.active_connections[device_name]
            try:
                await websocket.send(json.dumps(message))
                print(f"[AraConnectionManager] Sent message to '{device_name}'.")
            except websockets.exceptions.ConnectionClosed:
                print(f"[AraConnectionManager] Failed to send message to '{device_name}': Connection closed.")
                if device_name in self.active_connections:
                    del self.active_connections[device_name]
                self.bus.publish("child.disconnected",
                                 {"device_name": device_name, "reason": "send_failed_connection_closed"})
            except Exception as e:
                print(f"[AraConnectionManager] Failed to send message to '{device_name}': {e}")
        else:
            print(f"[AraConnectionManager] Device '{device_name}' not found in active connections.")
