from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("TierManager")

# Tier 0: No AI — basic motion rules only (fallback)
# Tier 1: iPad Neural Engine — YOLOv8 Nano, always on
# Tier 2: iPhone 14 Pro on WiFi — A18 Pro takes over inference


class SaiTierManager(AraService):
    """
    Stub for Phase 5 — manages which device runs AI inference.
    Tier 1 = iPad (default). Tier 2 = iPhone helper if available.
    """

    def __init__(self, bus):
        self.bus = bus
        self._status = "stopped"
        self._current_tier = 0  # Start at Tier 0 (no AI)
        self._helper_device = None

    def start(self):
        self._status = "running"
        self.bus.subscribe("session.created", self._check_helper)
        self.bus.subscribe("child.disconnected", self._check_helper_lost)
        log.info("Started at Tier %d.", self._current_tier)

    def stop(self):
        self._status = "stopped"
        self._current_tier = 0
        self._helper_device = None
        log.info("Stopped.")

    def status(self):
        return self._status

    def get_tier(self) -> int:
        return self._current_tier

    def get_processor(self) -> str:
        if self._current_tier == 2:
            return self._helper_device or "iphone"
        elif self._current_tier == 1:
            return "ipad"
        return "none"

    def _check_helper(self, data: dict):
        """
        When a new device connects, check if it's the AI helper (iPhone).
        Stub — checks device_type == "ios_helper" to promote to Tier 2.
        """
        device_type = data.get("device_type", "")
        device_name = data.get("device_name", "")

        if device_type == "ios_helper":
            self._helper_device = device_name
            self._current_tier = 2
            log.info("Tier 2 — '%s' is now AI processor.", device_name)

    def _check_helper_lost(self, data: dict):
        """If the helper disconnects, fall back to Tier 1 (or 0 if no model)."""
        device_name = data.get("device_name", "")
        if device_name == self._helper_device:
            self._helper_device = None
            self._current_tier = 1  # Fall back to iPad
            log.info("Helper lost. Fell back to Tier %d.", self._current_tier)
