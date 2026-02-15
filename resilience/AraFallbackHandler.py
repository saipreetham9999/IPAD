from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("FallbackHandler")


class AraFallbackHandler(AraService):
    """
    Phase 7 — handles service failures gracefully.
    When service.unhealthy fires, attempts recovery or alerts.
    """

    def __init__(self, bus, telegram_bot=None):
        self.bus = bus
        self.telegram_bot = telegram_bot
        self._status = "stopped"
        self._restart_map = {}  # { service_name: service_instance }

    def set_restart_map(self, service_map: dict):
        """Register services that can be restarted. { name: instance }"""
        self._restart_map = service_map

    def start(self):
        if self._status == "running":
            return
        self._status = "running"
        self.bus.subscribe("service.unhealthy", self._on_unhealthy)
        log.info("Started. %d services registered for auto-restart.", len(self._restart_map))

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _on_unhealthy(self, data: dict):
        services = data.get("services", [])
        for name in services:
            self._try_restart(name)

    def _try_restart(self, service_name: str):
        """Attempt to restart a failed service."""
        if service_name not in self._restart_map:
            log.warning("No restart handler for '%s'. Alerting.", service_name)
            self._alert(f"Service '{service_name}' unhealthy — no auto-restart available.")
            return

        service = self._restart_map[service_name]
        try:
            log.info("Restarting '%s'...", service_name)
            service.stop()
            service.start()
            log.info("'%s' restarted successfully.", service_name)
        except Exception as e:
            log.error("Failed to restart '%s': %s", service_name, e)
            self._alert(f"Service '{service_name}' failed to restart: {e}")

    def _alert(self, message: str):
        """Send critical failure alert via Telegram and bus."""
        self.bus.publish("alert.triggered", {
            "source": "FallbackHandler",
            "message": message,
        })
        if self.telegram_bot:
            self.telegram_bot.send_message(f"CRITICAL: {message}")
