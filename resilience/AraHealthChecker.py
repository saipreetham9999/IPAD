import threading
import time
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("HealthChecker")

CHECK_INTERVAL = 30  # seconds between health checks


class AraHealthChecker(AraService):
    """
    Phase 7 — periodically checks health of all registered services.
    If a service reports unhealthy, publishes service.unhealthy on the bus.
    """

    def __init__(self, bus, services: list = None):
        self.bus = bus
        self._services = services or []
        self._status = "stopped"
        self._running = False
        self._thread = None

    def set_services(self, services: list):
        """Called after Brain builds the service list."""
        self._services = services

    def start(self):
        if self._status == "running":
            return
        self._running = True
        self._status = "running"
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        log.info("Started. Checking %d services every %ds.", len(self._services), CHECK_INTERVAL)

    def stop(self):
        self._running = False
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _check_loop(self):
        while self._running:
            time.sleep(CHECK_INTERVAL)
            self._run_checks()

    def _run_checks(self):
        unhealthy = []
        for service in self._services:
            try:
                s = service.status()
                if s != "running":
                    name = service.__class__.__name__
                    unhealthy.append(name)
                    log.warning("%s is %s", name, s)
            except Exception as e:
                name = service.__class__.__name__
                unhealthy.append(name)
                log.error("%s health check failed: %s", name, e)

        if unhealthy:
            self.bus.publish("service.unhealthy", {
                "services": unhealthy,
                "count": len(unhealthy),
            })
        else:
            log.debug("All %d services healthy.", len(self._services))

    def get_report(self) -> dict:
        """Returns current health status of all services."""
        report = {}
        for service in self._services:
            name = service.__class__.__name__
            try:
                report[name] = service.status()
            except Exception:
                report[name] = "error"
        return report
