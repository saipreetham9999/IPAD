import requests
import time
import threading # Import threading
from core.AraService import AraService # Assuming AraService is PascalCase

class MiniTelegramBot(AraService):

    def __init__(self, settings, bus):
        self.settings = settings
        self.bus = bus
        self._status = "stopped"
        self._listener_thread = None # To hold the thread object
        self._running = False # Flag to control the listen loop
        self.offset = 0 # Initialize offset here

    def start(self):
        if not self._running:
            self._running = True
            self._status = "running"
            print("[MiniTelegramBot] Started. Initializing listener thread...")
            # Get initial offset before starting the listener thread
            self.offset = self._get_initial_offset()
            self._listener_thread = threading.Thread(target=self.listen, daemon=True)
            self._listener_thread.start()
            print("[MiniTelegramBot] Listener thread initiated.")

    def stop(self):
        if self._running:
            self._running = False # Set flag to stop the loop
            if self._listener_thread and self._listener_thread.is_alive():
                self._listener_thread.join(timeout=5) # Wait for thread to finish
            self._status = "stopped"
            print("[MiniTelegramBot] Stopped.")

    def status(self):
        return self._status

    def send_message(self, text):
        # Send message in a separate thread to avoid blocking the main app
        threading.Thread(
            target=self._send_message_worker,
            args=(text,),
            daemon=True
        ).start()

    def _send_message_worker(self, text):
        token = self.settings.TELEGRAM_TOKEN
        chat_id = self.settings.TELEGRAM_CHAT_ID

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            response = requests.post(url, json={
                "chat_id": chat_id,
                "text": text
            }, timeout=10) # Added timeout for robustness
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            print(f"[MiniTelegramBot] Message sent successfully: '{text}'")
        except requests.exceptions.HTTPError as http_err:
            print(f"[MiniTelegramBot] HTTP error occurred: {http_err}")
            if hasattr(http_err, 'response') and http_err.response is not None:
                print(f"[MiniTelegramBot] API response: {http_err.response.json()}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"[MiniTelegramBot] Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"[MiniTelegramBot] Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"[MiniTelegramBot] An unexpected request error occurred: {req_err}")
        except Exception as e:
            print(f"[MiniTelegramBot] An unexpected error occurred while sending message: {e}")

    def _get_initial_offset(self):
        """Fetches the latest update_id to start listening from new messages."""
        token = self.settings.TELEGRAM_TOKEN
        url = f"https://api.telegram.org/bot{token}/getUpdates?limit=1&timeout=0"
        try:
            response = requests.get(url, timeout=5).json() # Added timeout
            if response.get("ok") and response.get("result"):
                # Get the update_id of the last message + 1
                return response["result"][0]["update_id"] + 1
        except requests.exceptions.RequestException as e:
            print(f"[MiniTelegramBot] Error getting initial Telegram offset: {e}")
        return 0 # Default to 0 if something goes wrong

    def listen(self):
        token = self.settings.TELEGRAM_TOKEN
        current_offset = self.offset

        while self._running: # Use the running flag to control the loop
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates?offset={current_offset}"
                response = requests.get(url, timeout=10).json()

                for update in response.get("result", []):
                    current_offset = update["update_id"] + 1 # Update offset for next poll
                    if "message" in update and "text" in update["message"]:
                        message = update["message"]["text"]
                        print(f"[MiniTelegramBot] Received: {message}") # Added service prefix
                        self.bus.publish("telegram.command", message)

            except requests.exceptions.RequestException as e:
                print(f"[MiniTelegramBot] Error fetching Telegram updates: {e}")
            except Exception as e:
                print(f"[MiniTelegramBot] An unexpected error in listen loop: {e}")

            time.sleep(2) # Poll every 2 seconds