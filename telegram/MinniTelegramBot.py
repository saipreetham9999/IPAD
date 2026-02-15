import requests
import time
import threading
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
        token = self.settings.TELEGRAM_TOKEN
        current_offset = self.offset

        while self._running:
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates?offset={current_offset}"
                response = requests.get(url, timeout=10).json()

                for update in response.get("result", []):
                    current_offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        message = update["message"]["text"]
                        log.debug("Received: %s", message)
                        self.bus.publish("telegram.command", message)

            except requests.exceptions.RequestException as e:
                log.error("Error fetching updates: %s", e)
            except Exception as e:
                log.error("Unexpected error in listen loop: %s", e)

            time.sleep(2)
