"""
UPDATED MinniTelegramBot.py
Sends rich message data (with user_id, username, chat_id) instead of just text
Merge the listen() method with your existing code
"""

import requests
import time
import threading
import base64
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("TelegramBot")


class MiniTelegramBot(AraService):

    def __init__(self, settings, bus):
        self.settings = settings
        self.bus = bus
        self._status = "stopped"
        self._listener_thread = None
        self._running = False
        self.offset = 0

    def start(self):
        if not self._running:
            self._running = True
            self._status = "running"
            log.info("Started. Initializing listener...")
            self.offset = self._get_initial_offset()
            self._listener_thread = threading.Thread(target=self.listen, daemon=True)
            self._listener_thread.start()
            log.info("Listener thread running.")

    def stop(self):
        if self._running:
            self._running = False
            if self._listener_thread and self._listener_thread.is_alive():
                self._listener_thread.join(timeout=5)
            self._status = "stopped"
            log.info("Stopped.")

    def status(self):
        return self._status

    def send_message(self, text):
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
            }, timeout=10)
            response.raise_for_status()
            log.debug("Message sent: '%s'", text[:60])
        except requests.exceptions.HTTPError as e:
            log.error("HTTP error: %s", e)
        except requests.exceptions.ConnectionError as e:
            log.error("Connection error: %s", e)
        except requests.exceptions.Timeout:
            log.error("Timeout sending message")
        except Exception as e:
            log.error("Unexpected error sending message: %s", e)

    def send_photo(self, photo_data: str, caption: str = None):
        """
        Send a photo to the main group chat.
        
        Args:
            photo_data: Base64 encoded image string
            caption: Optional caption for the photo
        """
        threading.Thread(
            target=self._send_photo_worker,
            args=(photo_data, caption),
            daemon=True
        ).start()

    def _send_photo_worker(self, photo_data: str, caption: str):
        """Worker to upload and send photo"""
        token = self.settings.TELEGRAM_TOKEN
        chat_id = self.settings.TELEGRAM_CHAT_ID
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        
        try:
            # Clean up base64 string if it has header
            if "," in photo_data:
                photo_data = photo_data.split(",")[1]

            # Decode base64 to bytes
            image_bytes = base64.b64decode(photo_data)
            
            files = {
                "photo": ("image.jpg", image_bytes, "image/jpeg")
            }
            data = {
                "chat_id": chat_id
            }
            if caption:
                data["caption"] = caption

            response = requests.post(url, data=data, files=files, timeout=30)
            
            # Log response content if error
            if response.status_code != 200:
                log.error("Telegram API Error: %s", response.text)

            response.raise_for_status()
            log.debug("Photo sent to group with caption: %s", caption)
            
        except Exception as e:
            log.error("Failed to send photo: %s", e)

    def _get_initial_offset(self):
        token = self.settings.TELEGRAM_TOKEN
        url = f"https://api.telegram.org/bot{token}/getUpdates?limit=1&timeout=0"
        try:
            response = requests.get(url, timeout=5).json()
            if response.get("ok") and response.get("result"):
                return response["result"][0]["update_id"] + 1
        except requests.exceptions.RequestException as e:
            log.error("Error getting initial offset: %s", e)
        return 0

    def listen(self):
        """
        Listen for Telegram updates and publish rich message data
        """
        token = self.settings.TELEGRAM_TOKEN
        current_offset = self.offset

        while self._running:
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates?offset={current_offset}"
                response = requests.get(url, timeout=10).json()

                for update in response.get("result", []):
                    current_offset = update["update_id"] + 1

                    if "message" in update and "text" in update["message"]:
                        message_data = update["message"]
                        text = message_data["text"]

                        # Extract user info
                        user_id = message_data["from"]["id"]
                        username = message_data["from"].get("username", "unknown")
                        chat_id = message_data["chat"]["id"]

                        log.debug(
                            "Received from @%s (user_id=%d): %s",
                            username, user_id, text[:50]
                        )

                        # Publish rich message data
                        self.bus.publish("telegram.message", {
                            "text": text,
                            "user_id": user_id,
                            "username": username,
                            "chat_id": chat_id
                        })

            except requests.exceptions.RequestException as e:
                log.error("Error fetching updates: %s", e)
            except Exception as e:
                log.error("Unexpected error in listen loop: %s", e)

            time.sleep(2)

    def send_message_to_chat(self, chat_id: int, text: str):
        """Send to specific chat (user, group, anyone)"""
        threading.Thread(
            target=self._send_message_worker_to_chat,
            args=(chat_id, text),
            daemon=True
        ).start()

    def _send_message_worker_to_chat(self, chat_id: int, text: str):
        """Worker thread to send message to specific chat (non-blocking)"""
        token = self.settings.TELEGRAM_TOKEN
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            response = requests.post(url, json={
                "chat_id": chat_id,
                "text": text
            }, timeout=10)
            response.raise_for_status()
            log.debug("Message sent to chat %d: '%s'", chat_id, text[:60])
        except requests.exceptions.HTTPError as e:
            log.error("HTTP error sending to %d: %s", chat_id, e)
        except requests.exceptions.ConnectionError as e:
            log.error("Connection error sending to %d: %s", chat_id, e)
        except requests.exceptions.Timeout:
            log.error("Timeout sending to chat %d", chat_id)
        except Exception as e:
            log.error("Unexpected error sending to %d: %s", chat_id, e)
