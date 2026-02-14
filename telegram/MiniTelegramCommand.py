from core.AraService import AraService
from bus.JoBus import JoBus
from telegram.MinniTelegramBot import MiniTelegramBot
from children.AraChildManager import AraChildManager

class MiniTelegramCommand(AraService):
    def __init__(self, bus: JoBus, telegram_bot: MiniTelegramBot, child_manager: AraChildManager):
        self.bus = bus
        self.telegram_bot = telegram_bot
        self.child_manager = child_manager
        self._status = "stopped"

    def start(self):
        if self._status == "running":
            return
        self._status = "running"
        print("[TelegramCommand] Started.")
        self.bus.subscribe("telegram.command", self._handle_telegram_command)

    def stop(self):
        self._status = "stopped"
        print("[TelegramCommand] Stopped.")
        # Optionally unsubscribe

    def status(self):
        return self._status

    def _handle_telegram_command(self, command_text: str):
        print(f"[TelegramCommand] Received command: {command_text}")
        if command_text == "/status":
            self._send_status_report()
        elif command_text == "/hello":
            self.telegram_bot.send_message("Hello there! How can I help you?")
        else:
            # For now, do nothing for unknown commands
            pass

    def _send_status_report(self):
        active_children = self.child_manager.get_all()
        child_count = len(active_children)

        report = "🧠 Brain Status: Online\n"
        report += f"🔗 Connected Children: {child_count}\n"

        if child_count > 0:
            report += "\nActive Devices:\n"
            for device_name, child_data in active_children.items():
                device_type = child_data.get("device_type", "Unknown")
                session_id = child_data.get("session_id", "N/A")

                report += (
                    f"- {device_name} "
                    f"(Type: {device_type}, "
                    f"Session ID: {session_id})\n"
                )

        self.telegram_bot.send_message(report)
