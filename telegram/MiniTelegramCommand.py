"""
MiniTelegramCommand.py - COMPLETE & CORRECTED
Handles both Brain commands and Chat commands
All model names corrected for OpenRouter
"""

from core.AraService import AraService
from bus.JoLogger import get_logger
from telegram.MinniTelegramBot import MiniTelegramBot
from children.AraChildManager import AraChildManager
from bus.JoBus import JoBus

log = get_logger("TelegramCommand")


class MiniTelegramCommand(AraService):
    """
    Telegram command handler
    - Handles brain commands: /status, /hello, /children
    - Handles chat commands: /chat_start, /chat_end, /chat_status, /chat_help
    - Routes regular messages to chat orchestrator
    """

    def __init__(self, bus: JoBus, telegram_bot: MiniTelegramBot, child_manager: AraChildManager):
        self.bus = bus
        self.telegram_bot = telegram_bot
        self.child_manager = child_manager
        self._status = "stopped"

    def start(self):
        """Start the service"""
        if self._status == "running":
            return
        self._status = "running"
        log.info("Started.")
        self.bus.subscribe("telegram.message", self._on_message)
        self.bus.subscribe("alert.triggered", self._on_alert)

    def stop(self):
        """Stop the service"""
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        """Get service status"""
        return self._status

    # ========================================================================
    # Main message handler
    # ========================================================================

    def _on_message(self, data: dict):
        """
        Handle telegram message with rich data.
        If the message starts with '/', it's a command.
        Otherwise, it's a chat message.

        Expected data:
        {
            "text": "message text",
            "user_id": 123456,
            "username": "john_doe",
            "chat_id": 789012
        }
        """
        text = data.get("text", "")
        user_id = data.get("user_id")
        username = data.get("username", "unknown")
        chat_id = data.get("chat_id")

        if not text or not user_id or not chat_id:
            log.warning("Invalid message data: %s", data)
            return

        log.debug("Message from @%s: %s", username, text[:50])

        # If starts with /, it's a command
        if text.startswith("/"):
            self._handle_command(text, user_id, username, chat_id)
        else:
            # Regular chat message - publish for orchestrator
            self.bus.publish("telegram.chat_message", {
                "user_id": user_id,
                "username": username,
                "message": text,
                "chat_id": chat_id
            })

    # ========================================================================
    # Command handler
    # ========================================================================

    def _handle_command(self, command_text: str, user_id: int, username: str, chat_id: int):
        """
        Handle telegram commands

        Brain commands:
        - /status - Show brain status
        - /hello - Greet user
        - /children - List connected devices

        Chat commands:
        - /chat_start [model] - Start chat session
        - /chat_end - End chat session
        - /chat_status - Show chat system status
        - /chat_help - Show chat help
        """
        log.debug("Command: %s from @%s", command_text, username)
        command = command_text.strip().lower()

        # --- Brain commands ---
        if command == "/status":
            self._send_status_report()

        elif command == "/hello":
            self.telegram_bot.send_message_to_chat(
                chat_id,
                "Hello! Brain is online. Use /chat_start to begin a conversation."
            )

        elif command == "/children":
            self._send_children_list(chat_id)

        # --- Chat commands ---
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
            msg += "Use /chat_start to begin a conversation or /chat_help for more options."
            self.telegram_bot.send_message_to_chat(chat_id, msg)

    # ========================================================================
    # Brain commands
    # ========================================================================

    def _on_alert(self, data: dict):
        """
        Handle alerts - sends to main Telegram group (not user chat)
        """
        source = data.get("source", "unknown")
        message = data.get("message", "Alert triggered")
        self.telegram_bot.send_message(f"ALERT [{source}]: {message}")
        log.info("Alert sent to Telegram: %s", message[:60])

    def _send_status_report(self):
        """
        Send brain status report to main group
        Shows: online/offline, connected devices count
        """
        children = self.child_manager.get_all()
        count = len(children)

        report = f"Brain Status: Online\n"
        report += f"Connected Children: {count}\n"

        if count > 0:
            report += "\nActive Devices:\n"
            for name, data in children.items():
                device_type = data.get("device_type", "Unknown")
                report += f"  - {name} ({device_type})\n"
        else:
            report += "\nNo children connected."

        self.telegram_bot.send_message(report)

    def _send_children_list(self, chat_id: int):
        """
        Send list of connected devices to user chat
        """
        children = self.child_manager.get_all()

        if not children:
            self.telegram_bot.send_message_to_chat(chat_id, "No children connected.")
            return

        msg = "Connected devices:\n"
        for name, data in children.items():
            device_type = data.get("device_type", "?")
            msg += f"  - {name} ({device_type})\n"

        self.telegram_bot.send_message_to_chat(chat_id, msg)

    # ========================================================================
    # Chat commands
    # ========================================================================

    def _handle_chat_start(self, command_text: str, user_id: int, username: str, chat_id: int):
        """
        Handle /chat_start [model] command

        Usage:
        /chat_start           - Start with Mistral (default)
        /chat_start llama     - Start with Llama
        /chat_start qwen      - Start with Qwen
        """
        parts = command_text.split()
        model_alias = parts[1].lower() if len(parts) > 1 else "mistral"

        # CORRECTED MODEL NAMES
        model_map = {
            "mistral": "arcee-ai/trinity-large-preview:free",
            "llama": "meta-llama/llama-3-8b-instruct:free",
            "qwen": "qwen/qwen-7b-chat:free"
        }

        model = model_map.get(model_alias, model_map["mistral"])

        log.info("Chat start requested: @%s with %s", username, model_alias)

        # Publish start request for orchestrator
        self.bus.publish("chat.start_request", {
            "user_id": user_id,
            "username": username,
            "model": model,
            "chat_id": chat_id
        })

    def _handle_chat_end(self, user_id: int, username: str, chat_id: int):
        """
        Handle /chat_end command
        Ends the user's chat session
        """
        log.info("Chat end requested: @%s", username)

        self.bus.publish("chat.end_request", {
            "user_id": user_id,
            "username": username,
            "chat_id": chat_id
        })

    def _handle_chat_status(self, chat_id: int):
        """
        Handle /chat_status command
        Shows chat system status and active sessions
        """
        log.info("Chat status requested")

        self.bus.publish("chat.status_request", {
            "chat_id": chat_id
        })

    def _handle_chat_help(self, chat_id: int):
        """
        Handle /chat_help command
        Shows available chat commands and usage
        """
        msg = """AI Chat Help

Commands:
/chat_start [model]  Start a chat session
  Models: mistral (default), llama, qwen

/chat_end            End current chat

/chat_status         Show system status

/chat_help           Show this help

Brain Commands:
/status              Show brain status
/children            List connected devices
/hello               Greet the bot

After starting a chat, just type a message!

Example:
/chat_start
What is the capital of France?
/chat_end"""

        self.telegram_bot.send_message_to_chat(chat_id, msg)
