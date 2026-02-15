from brain.settings import Settings
from bus.JoBus import JoBus
from children.AraChildManager import AraChildManager
from core.AraSessionmanager import AraSessionManager
from network.AraConnectionManager import AraConnectionManager
from telegram.MiniTelegramCommand import MiniTelegramCommand
from telegram.MinniTelegramBot import MiniTelegramBot


class Brain:

    def __init__(self):
        self.settings = Settings()
        self.bus = JoBus()

        # Phase 1 Services
        self.telegram_bot = MiniTelegramBot(
            settings=self.settings,
            bus=self.bus
        )

        # Phase 2 Services
        self.connection_manager = AraConnectionManager(
            bus=self.bus,
            host="0.0.0.0",
            port=8765
        )
        self.session_manager = AraSessionManager(
            bus=self.bus
        )
        self.child_manager = AraChildManager(
            bus=self.bus
        )
        self.telegram_command_handler = MiniTelegramCommand(
            bus=self.bus,
            telegram_bot=self.telegram_bot,
            child_manager=self.child_manager
        )

        # All services managed by the Brain
        self.services = [
            self.telegram_bot,
            self.connection_manager,
            self.session_manager,
            self.child_manager,
            self.telegram_command_handler
        ]

    def start(self):
        print("🧠 BRAIN BOOTING...\n")
        print("[Brain.start] Starting all registered services...") # Diagnostic print

        for service in self.services:
            service.start()
            print(f"[Brain.start] {service.__class__.__name__} started") # More detailed print

        print("[Brain.start] All services initiated.") # Diagnostic print
        print("\n🟢 BRAIN ONLINE")
        # Send Telegram message AFTER all services have started
        self.telegram_bot.send_message("🟢 Brain Online")

    def stop(self):
        for service in reversed(self.services):
            service.stop()
