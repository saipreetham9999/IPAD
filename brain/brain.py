from brain.settings import Settings
from bus.JoBus import JoBus
from bus.JoLogger import get_logger
from children.AraChildManager import AraChildManager
from core.AraSessionmanager import AraSessionManager
from network.AraConnectionManager import AraConnectionManager
from notifications.MinniMessegeRouter import MiniMessageRouter
from sai.SaiChatOrchestrator import SaiChatOrchestrator
from sai.SaiChatSessionManager import SaiChatSessionManager
from sai.SaiOpenRouterClient import SaiOpenRouterClient
from telegram.MiniTelegramCommand import MiniTelegramCommand
from telegram.MinniTelegramBot import MiniTelegramBot

# Phase 5 — AI stubs
from sai.SaiVisionEngine import SaiVisionEngine
from sai.SaiModelStore import SaiModelStore
from sai.SaiTierManager import SaiTierManager
from sai.SaiAlertRules import SaiAlertRules

# Phase 6 — Memory
from memory.JoEventLogger import JoEventLogger
from memory.SaiSnapshotManager import SaiSnapshotManager

# Phase 7 — Resilience
from resilience.AraHealthChecker import AraHealthChecker
from resilience.AraReconnectManager import AraReconnectManager
from resilience.AraFallbackHandler import AraFallbackHandler

# Phase 8 — Shields
from shields.AraWatchdog import AraWatchdog

log = get_logger("Brain")


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

        # Phase 3 — Telegram commands + alerts only
        self.telegram_command = MiniTelegramCommand(
            bus=self.bus,
            telegram_bot=self.telegram_bot,
            child_manager=self.child_manager
        )

        # Phase 4 — Message routing to children
        self.message_router = MiniMessageRouter(bus=self.bus)

        # Phase 5 — AI (stubs)
        self.model_store = SaiModelStore()
        self.alert_rules = SaiAlertRules(bus=self.bus)
        self.tier_manager = SaiTierManager(bus=self.bus)
        self.vision_engine = SaiVisionEngine(
            bus=self.bus,
            tier_manager=self.tier_manager,
            alert_rules=self.alert_rules
        )
        self.openrouter_client = SaiOpenRouterClient(
            api_key=self.settings.OPENROUTER_API_KEY
        )
        self.chat_session_manager = SaiChatSessionManager(
            bus=self.bus,
            max_users=20,  # Max 20 concurrent users
            idle_timeout_seconds=1800  # 30 minutes
        )
        self.chat_orchestrator = SaiChatOrchestrator(
            bus=self.bus,
            session_manager=self.chat_session_manager,
            openrouter_client=self.openrouter_client,
            telegram_bot=self.telegram_bot,
            settings=self.settings
        )

        # Phase 6 — Memory
        self.event_logger = JoEventLogger(bus=self.bus)
        self.snapshot_manager = SaiSnapshotManager(bus=self.bus)

        # Phase 7 — Resilience
        self.reconnect_manager = AraReconnectManager(bus=self.bus)
        self.health_checker = AraHealthChecker(bus=self.bus)
        self.fallback_handler = AraFallbackHandler(
            bus=self.bus,
            telegram_bot=self.telegram_bot
        )

        # Phase 8 — Shields
        self.watchdog = AraWatchdog(bus=self.bus, telegram_bot=self.telegram_bot)

        # Boot order: core -> telegram -> routing -> AI -> memory -> resilience -> shields
        self.services = [
            self.telegram_bot,
            self.connection_manager,
            self.session_manager,
            self.child_manager,
            self.telegram_command,
            self.message_router,

            # Phase 5 — AI
            self.model_store,
            self.alert_rules,
            self.tier_manager,
            self.vision_engine,

            # Phase 5 — Chat (NEW)
            self.chat_session_manager,
            self.chat_orchestrator,

            # Phase 6 — Memory
            self.event_logger,
            self.snapshot_manager,

            # Phase 7 — Resilience
            self.reconnect_manager,
            self.health_checker,
            self.fallback_handler,

            # Phase 8 — Shields
            self.watchdog,
        ]

        # Wire health checker with the full service list
        self.health_checker.set_services(self.services)

        # Wire fallback handler with restartable services
        self.fallback_handler.set_restart_map({
            s.__class__.__name__: s for s in self.services
        })

    def start(self):
        log.info("BRAIN BOOTING...")
        for service in self.services:
            service.start()
            log.info("  %s started", service.__class__.__name__)
        log.info("BRAIN ONLINE — %d services running", len(self.services))
        self.telegram_bot.send_message("Brain Online — all systems ready")

    def stop(self):
        log.info("BRAIN SHUTTING DOWN...")
        for service in reversed(self.services):
            service.stop()
        log.info("Brain stopped.")
