# New import
from brain.settings import Settings
from bus.JoBus import JoBus
from children.AraChildManager import AraChildManager
from core.AraSessionmanager import AraSessionManager
from network.AraConnectionManager import AraConnectionManager
from telegram.MinniTelegramBot import MiniTelegramBot


class MiniTelegramCommand:
    pass


class Brain:

    def __init__(self):
        self.settings = Settings()
        self.bus = JoBus()

        # Phase 1 Services
        self.telegram_bot = MiniTelegramBot( # Renamed from 'telegram' to avoid conflict with module name
            settings=self.settings,
            bus=self.bus
        )

        # Phase 2 Services
        self.connection_manager = AraConnectionManager(
            bus=self.bus,
            host="0.0.0.0",
            port=8000
        )
        self.session_manager = AraSessionManager(
            bus=self.bus
        )
        self.child_manager = AraChildManager(
            bus=self.bus
        )
        # self.telegram_command_handler = MiniTelegramCommand(
        #     bus=self.bus,
        #     telegram_bot=self.telegram_bot,
        #     child_manager=self.child_manager
        # )

        # All services managed by the Brain
        self.services = [
            self.telegram_bot,
            self.connection_manager,
            self.session_manager,
            self.child_manager
            # self.telegram_command_handler
        ]

        # The _setup_command_handlers and _handle_telegram_command methods are removed
        # from Brain, as MiniTelegramCommand now handles this.

    def start(self):
        print("🧠 BRAIN BOOTING...\n")
        print("[Brain.start] Starting all registered services...") # Diagnostic print
        self.telegram_bot.send_message("🟢 Brain Online")
        for service in self.services:
            service.start()
            print(f"[Brain.start] {service.__class__.__name__} started") # More detailed print
        # Send Telegram message AFTER all services have start

    def stop(self):
        for service in reversed(self.services):
            service.stop()
