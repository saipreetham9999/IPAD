from brain.settings import Settings
from bus.JoBus import JoBus
from children.AraChildManager import AraChildManager
from core.AraSessionmanager import AraSessionManager
from network.AraConnectionManager import AraConnectionManager
from notifications.MinniMessegeRouter import MiniMessageRouter
from telegram.MiniTelegramCommand import MiniTelegramCommand
from telegram.MinniTelegramBot import MiniTelegramBot


class Brain:

    def __init__(self):
        self.settings = Settings()
        self.bus = JoBus()

        # Phase 1 — Heart
        self.telegram_bot = MiniTelegramBot(
            settings=self.settings,
            bus=self.bus
        )

        # Phase 2 — Spine
        self.connection_manager = AraConnectionManager(bus=self.bus)
        self.session_manager = AraSessionManager(bus=self.bus)
        self.child_manager = AraChildManager(bus=self.bus)

        # Phase 3 — Telegram always on + child notifications
        self.telegram_command = MiniTelegramCommand(
            bus=self.bus,
            telegram_bot=self.telegram_bot,
            child_manager=self.child_manager
        )

        # Phase 4 — Message routing to children
        self.message_router = MiniMessageRouter(bus=self.bus)

        # Boot order matters — core first, then telegram, then routing
        self.services = [
            self.telegram_bot,
            self.connection_manager,
            self.session_manager,
            self.child_manager,
            self.telegram_command,
            self.message_router,
        ]

    def start(self):
        print("🧠 BRAIN BOOTING...\n")
        for service in self.services:
            service.start()
            print(f"  ✅ {service.__class__.__name__} started")
        print("\n🟢 BRAIN ONLINE")
        self.telegram_bot.send_message("🟢 Brain Online — all systems ready")

    def stop(self):
        print("🔴 BRAIN SHUTTING DOWN...")
        for service in reversed(self.services):
            service.stop()
        print("Brain stopped.")