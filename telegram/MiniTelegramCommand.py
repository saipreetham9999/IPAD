from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("TelegramCommand")


class MiniTelegramCommand(AraService):

    def __init__(self, bus, telegram_bot, child_manager):
        self.bus = bus
        self.telegram_bot = telegram_bot
        self.child_manager = child_manager
        self._status = "stopped"

    def start(self):
        if self._status == "running":
            return
        self._status = "running"
        log.info("Started.")
        self.bus.subscribe("telegram.command", self._handle_command)
        # Alerts only — no connect/disconnect noise to Telegram
        self.bus.subscribe("alert.triggered", self._on_alert)

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    # -- Telegram commands -----------------------------------------------
    def _handle_command(self, command_text: str):
        log.debug("Command: %s", command_text)
        command = command_text.strip().lower()

        if command == "/status":
            self._send_status_report()
        elif command == "/hello":
            self.telegram_bot.send_message("Hello! Brain is online and listening.")
        elif command == "/children":
            self._send_children_list()
        else:
            self.telegram_bot.send_message(f"Unknown command: {command_text}")

    # -- Alerts only — per spec ------------------------------------------
    def _on_alert(self, data: dict):
        source = data.get("source", "unknown")
        message = data.get("message", "Alert triggered")
        self.telegram_bot.send_message(f"ALERT [{source}]: {message}")
        log.info("Alert sent to Telegram: %s", message[:60])

    # -- Status report ---------------------------------------------------
    def _send_status_report(self):
        children = self.child_manager.get_all()
        count = len(children)

        report = "Brain Status: Online\n"
        report += f"Connected Children: {count}\n"

        if count > 0:
            report += "\nActive Devices:\n"
            for name, data in children.items():
                device_type = data.get("device_type", "Unknown")
                report += f"  - {name} ({device_type})\n"
        else:
            report += "\nNo children connected."

        self.telegram_bot.send_message(report)

    def _send_children_list(self):
        children = self.child_manager.get_all()
        if not children:
            self.telegram_bot.send_message("No children connected.")
            return
        msg = "Connected devices:\n"
        for name, data in children.items():
            msg += f"  - {name} ({data.get('device_type', '?')})\n"
        self.telegram_bot.send_message(msg)
