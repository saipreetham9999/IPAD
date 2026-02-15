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
        print("[MiniTelegramCommand] Started.")
        self.bus.subscribe("telegram.command", self._handle_command)
        self.bus.subscribe("session.created", self._on_child_connected)
        self.bus.subscribe("child.disconnected", self._on_child_disconnected)

    def stop(self):
        self._status = "stopped"
        print("[MiniTelegramCommand] Stopped.")

    def status(self):
        return self._status

    # ── Telegram commands ─────────────────────────────────────────────
    def _handle_command(self, command_text: str):
        print(f"[MiniTelegramCommand] Command: {command_text}")
        command = command_text.strip().lower()

        if command == "/status":
            self._send_status_report()
        elif command == "/hello":
            self.telegram_bot.send_message("Hello! Brain is online and listening.")
        elif command == "/children":
            self._send_children_list()
        else:
            self.telegram_bot.send_message(f"Unknown command: {command_text}")

    # ── Child events → Telegram ───────────────────────────────────────
    def _on_child_connected(self, data: dict):
        device_name = data.get("device_name", "Unknown")
        device_type = data.get("device_type", "Unknown")
        self.telegram_bot.send_message(
            f"🟢 {device_name} connected\n"
            f"Type: {device_type}"
        )

    def _on_child_disconnected(self, data: dict):
        device_name = data.get("device_name", "Unknown")
        reason = data.get("reason", "unknown")
        self.telegram_bot.send_message(
            f"🔴 {device_name} disconnected\n"
            f"Reason: {reason}"
        )

    # ── Status report ─────────────────────────────────────────────────
    def _send_status_report(self):
        children = self.child_manager.get_all()
        count = len(children)

        report = "🧠 Brain Status: Online\n"
        report += f"🔗 Connected Children: {count}\n"

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