
import requests
import time
from core.ara_service import AraService

class MiniTelegramBot(AraService):

    def __init__(self, settings, bus):
        self.settings = settings
        self.bus = bus

    def start(self):
        self._status = "running"
        print("Telegram bot started")
        self.listen()

    def stop(self):
        self._status = "stopped"

    def status(self):
        return self._status

    def send_message(self, text):
        token = self.settings.TELEGRAM_TOKEN
        chat_id = self.settings.TELEGRAM_CHAT_ID

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id,
            "text": text
        })

    def listen(self):
        token = self.settings.TELEGRAM_TOKEN

        while True:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            response = requests.get(url).json()

            for update in response.get("result", []):
                self.offset = update["update_id"] + 1
                message = update["message"]["text"]

                print("Received:", message)

                # publish to bus
                self.bus.publish("telegram.command", message)

            time.sleep(2)
