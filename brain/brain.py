from brain.settings import Settings
from bus.jo_bus import JoBus
from telegram.mini_telegram_bot import MiniTelegramBot


class Brain:

    def __init__(self):
        self.settings = Settings()
        self.bus = JoBus()

        self.telegram = MiniTelegramBot(
            settings=self.settings,
            bus=self.bus
        )

        self.services = [
            self.telegram
        ]

    def start(self):
        print("🧠 BRAIN BOOTING...\n")

        for service in self.services:
            service.start()
            print(f"{service.__class__.__name__} started")

        print("\n🟢 BRAIN ONLINE")
        # Send Telegram message when Brain is online
        self.telegram.send_message("🟢 Brain Online")

    def stop(self):
        for service in reversed(self.services):
            service.stop()
