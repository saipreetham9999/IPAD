"""
UPDATED MiniTelegramCommand.py
Integrates OpenRouter chat commands with existing command handler
Merge this with your existing MiniTelegramCommand
"""

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

        # OLD: Listen for simple command strings
        # self.bus.subscribe("telegram.command", self._handle_command)

        # NEW: Listen for rich message data (from updated MinniTelegramBot)
        self.bus.subscribe("telegram.message", self._on_message)

        # Alerts only — no connect/disconnect noise to Telegram
        self.bus.subscribe("alert.triggered", self._on_alert)

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    # ========================================================================
    # UPDATED: Handle rich message data from MinniTelegramBot
    # ========================================================================

    def _on_message(self, data: dict):
        """
        Handle telegram message with rich data

        Expected data:
        {
            "text": "/status",
            "user_id": 123456,
            "username": "john_doe",
            "chat_id": 789012
        }
        """
        text = data.get("text", "")
        user_id = data.get("user_id")
        username = data.get("username", "unknown")
        chat_id = data.get("chat_id")

        if not text:
            return

        log.debug("Message from @%s: %s", username, text[:50])

        # If starts with /, it's a command
        if text.startswith("/"):
            self._handle_command(text, user_id, username, chat_id)
        # Otherwise, route to chat
        else:
            self.bus.publish("telegram.chat_message", {
                "user_id": user_id,
                "username": username,
                "message": text,
                "chat_id": chat_id
            })

    # ========================================================================
    # Command handler (updated to handle chat commands)
    # ========================================================================

    def _handle_command(self, command_text: str, user_id: int = None,
                        username: str = None, chat_id: int = None):
        """
        Handle telegram commands
        Supports both old format (string only) and new format (with user data)
        """
        log.debug("Command: %s from @%s", command_text, username)
        command = command_text.strip().lower()

        # --- Brain status commands ---
        if command == "/status":
            self._send_status_report()

        elif command == "/hello":
            self.telegram_bot.send_message("Hello! Brain is online and listening.")

        elif command == "/children":
            self._send_children_list()

        # --- Chat commands (NEW) ---
        elif command.startswith("/chat_start"):
            self._handle_chat_start(command_text, user_id, username, chat_id)

        elif command.startswith("/chat_end"):
            self._handle_chat_end(user_id, username, chat_id)

        elif command == "/chat_status":
            self._handle_chat_status(chat_id)

        elif command == "/chat_help":
            self._handle_chat_help(chat_id)

        # --- Unknown command ---
        else:
            msg = f"Unknown command: {command_text}\n\n"
            msg += "Available commands:\n"
            msg += "/status - Brain status\n"
            msg += "/children - Connected devices\n"
            msg += "/chat_start - Start AI chat\n"
            msg += "/chat_end - End AI chat\n"
            msg += "/chat_status - Chat system status\n"
            msg += "/chat_help - Chat help"
            self.telegram_bot.send_message(msg)

    # ========================================================================
    # Brain status commands (existing)
    # ========================================================================

    def _on_alert(self, data: dict):
        """Alerts only — per spec"""
        source = data.get("source", "unknown")
        message = data.get("message", "Alert triggered")
        self.telegram_bot.send_message(f"ALERT [{source}]: {message}")
        log.info("Alert sent to Telegram: %s", message[:60])

    def _send_status_report(self):
        """Show brain status"""
        children = self.child_manager.get_all()
        count = len(children)

        report = "🧠 Brain Status: Online\n"
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
        """List connected devices"""
        children = self.child_manager.get_all()
        if not children:
            self.telegram_bot.send_message("No children connected.")
            return
        msg = "📱 Connected devices:\n"
        for name, data in children.items():
            msg += f"  - {name} ({data.get('device_type', '?')})\n"
        self.telegram_bot.send_message(msg)

    # ========================================================================
    # Chat commands (NEW) — publish to bus for orchestrator to handle
    # ========================================================================

    def _handle_chat_start(self, command_text: str, user_id: int,
                           username: str, chat_id: int):
        """
        Handle /chat_start [model]
        Models: mistral (default), llama, qwen
        """
        parts = command_text.split()
        model_alias = parts[1].lower() if len(parts) > 1 else "mistral"

        # Map alias to full model name
        model_map = {
            "mistral": "mistralai/mistral-7b:free",
            "llama": "meta-llama/llama-3-8b-instruct:free",
            "qwen": "qwen/qwen-7b-chat:free"
        }

        model = model_map.get(model_alias, model_map["mistral"])

        log.info("Chat start requested: @%s with %s", username, model_alias)

        # Publish to bus for orchestrator to handle
        self.bus.publish("chat.start_request", {
            "user_id": user_id,
            "username": username,
            "model": model,
            "chat_id": chat_id
        })

    def _handle_chat_end(self, user_id: int, username: str, chat_id: int):
        """Handle /chat_end"""
        log.info("Chat end requested: @%s", username)
        self.bus.publish("chat.end_request", {
            "user_id": user_id,
            "username": username,
            "chat_id": chat_id
        })

    def _handle_chat_status(self, chat_id: int):
        """Handle /chat_status"""
        log.info("Chat status requested")
        self.bus.publish("chat.status_request", {
            "chat_id": chat_id
        })

    def _handle_chat_help(self, chat_id: int):
        """Handle /chat_help"""
        msg = """🤖 AI Chat Help

Commands:
/chat_start [model]  Start a chat session
  Models: mistral (default), llama, qwen

/chat_end            End current chat

/chat_status         Show system status

/chat_help           Show this help

Just type a message to chat after /chat_start!

Examples:
  /chat_start
  What is the capital of France?
  /chat_end"""

        self.telegram_bot.send_message(msg)