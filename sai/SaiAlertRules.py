from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("AlertRules")

CONFIDENCE_THRESHOLD = 0.7


class SaiAlertRules(AraService):
    """
    Stub for Phase 5 — detection policies and alert rules.
    Evaluates AI decisions and decides whether to fire alert.triggered.
    """

    def __init__(self, bus):
        self.bus = bus
        self._status = "stopped"
        self.confidence_threshold = CONFIDENCE_THRESHOLD

    def start(self):
        self._status = "running"
        log.info("Started. Confidence threshold: %.1f", self.confidence_threshold)

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def should_alert(self, decision: dict) -> bool:
        """
        Evaluates a decision object from VisionEngine.
        Returns True if an alert should fire.

        Rules:
        - confidence < threshold → discard, no alert
        - person_present and anomaly → alert
        - motion_level > 0.8 and anomaly → alert
        """
        confidence = decision.get("confidence", 0.0)

        if confidence < self.confidence_threshold:
            log.debug("Discarded: confidence %.2f < %.2f", confidence, self.confidence_threshold)
            return False

        if decision.get("person_present") and decision.get("anomaly"):
            return True

        if decision.get("motion_level", 0) > 0.8 and decision.get("anomaly"):
            return True

        return False

    def fire_alert(self, decision: dict, device_name: str = "unknown"):
        """Publishes alert.triggered if rules pass."""
        if self.should_alert(decision):
            alert = {
                "source": device_name,
                "message": f"Person detected (count={decision.get('count', 0)}, zone={decision.get('zone')})",
                "confidence": decision.get("confidence"),
                "decision": decision,
            }
            self.bus.publish("alert.triggered", alert)
            log.info("Alert fired for '%s'", device_name)
