from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("VisionEngine")

# Decision object shape — always returned from process_frame()
EMPTY_DECISION = {
    "person_present": False,
    "count": 0,
    "zone": None,
    "motion_level": 0.0,
    "anomaly": False,
    "confidence": 0.0,
    "processed_by": "none",
}


class SaiVisionEngine(AraService):
    """
    Stub for Phase 5 — runs inference on camera frames.
    When real AI is wired, this calls SaiModelStore.predict() and
    SaiAlertRules.evaluate() then publishes alert.triggered via bus.
    """

    def __init__(self, bus, tier_manager=None, alert_rules=None):
        self.bus = bus
        self.tier_manager = tier_manager
        self.alert_rules = alert_rules
        self._status = "stopped"

    def start(self):
        self._status = "running"
        self.bus.subscribe("child.report.received", self._on_report)
        log.info("Started (stub mode — no model loaded).")

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _on_report(self, data: dict):
        """
        Called when a child sends a frame/report.
        Stub: logs it, returns empty decision, does not fire alert.
        """
        device = data.get("device_name", "unknown")
        log.debug("Report from '%s' — stub, no inference.", device)
        # When real model is loaded, this would be:
        #   decision = self.process_frame(data.get("frame"))
        #   if self.alert_rules and self.alert_rules.should_alert(decision):
        #       self.bus.publish("alert.triggered", {...})

    def process_frame(self, frame_data) -> dict:
        """
        Stub — returns empty decision.
        Override when CoreML/YOLO is available.
        """
        return dict(EMPTY_DECISION)
