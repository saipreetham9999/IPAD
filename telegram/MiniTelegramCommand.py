"""
MiniTelegramCommand.py
Telegram command handler - no emojis, clean logging
"""

from core.AraService import AraService
from bus.JoLogger import get_logger
from telegram.MinniTelegramBot import MiniTelegramBot
from children.AraChildManager import AraChildManager
from bus.JoBus import JoBus

log = get_logger("TelegramCommand")


class MiniTelegramCommand(AraService):
    """Telegram command handler"""

    def __init__(self, bus: JoBus, telegram_bot: MiniTelegramBot, child_manager: AraChildManager):
        self.bus = bus
        self.telegram_bot = telegram_bot
        self.child_manager = child_manager
        self._status = "stopped"

    def start(self):
        self._status = "running"
        log.info("Started")
        self.bus.subscribe("telegram.message", self._on_message)
        self.bus.subscribe("alert.triggered", self._on_alert)
        self.bus.subscribe("vision.analysis.result", self._on_vision_result)

    def stop(self):
        self._status = "stopped"
        log.info("Stopped")

    def status(self):
        return self._status

    # ========================================================================
    # Main message handler
    # ========================================================================

    def _on_message(self, data: dict):
        """Handle incoming telegram message"""

        text = data.get("text", "")
        user_id = data.get("user_id")
        username = data.get("username", "unknown")
        chat_id = data.get("chat_id")
        if not text or not user_id or not chat_id:
            return

        if text.startswith("/"):
            self._handle_command(text, user_id, username, chat_id)
        else:
            # Check for model selection (1-7)
            if text.strip().isdigit():
                model_num = int(text.strip())
                if 1 <= model_num <= 7:
                    self._handle_model_selection(model_num, user_id, username, chat_id)
                    return

            # Regular chat message
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
        """Handle / commands"""
        log.info("Command %s", command_text)
        command = command_text.strip().lower()
        if command == "/status":
            self._send_status_report()
        elif command == "/hello":
            self.telegram_bot.send_message_to_chat(
                chat_id,
                "Hello! Brain is online."
            )

        elif command == "/children":
            self._send_children_list(chat_id)

        elif command.startswith("/chat_start"):
            self._handle_chat_start(user_id, username, chat_id)

        elif command.startswith("/chat_end"):
            self._handle_chat_end(user_id, username, chat_id)

        elif command == "/chat_status":
            self._handle_chat_status(chat_id)

        elif command == "/chat_help":
            self._handle_chat_help(chat_id)

        else:
            self.telegram_bot.send_message_to_chat(chat_id, f"Unknown command: {command_text}")

    # ========================================================================
    # Brain commands
    # ========================================================================

    def _on_alert(self, data: dict):
        """Handle alerts"""
        source = data.get("source", "unknown")
        message = data.get("message", "Alert triggered")

        if source.startswith("Vision"):
            return

        self.telegram_bot.send_message(f"ALERT [{source}]: {message}")

    def _on_vision_result(self, data: dict):
        """Handle vision analysis results"""
        device = data.get("device", "unknown")
        description = data.get("description", "No description")
        image_data = data.get("image_data")
        
        caption = f"[{device}] Vision Analysis:\n{description}"
        
        if image_data:
            self.telegram_bot.send_photo(image_data, caption)
        else:            self.telegram_bot.send_message(caption)

    def _send_status_report(self):
        """Send brain status"""
        children = self.child_manager.get_all()
        count = len(children)

        report = f"Brain Status: Online\n"
        report += f"Connected Children: {count}\n"

        if count > 0:
            report += "\nDevices:\n"
            for name, data in children.items():
                device_type = data.get("device_type", "Unknown")
                report += f"  - {name} ({device_type})\n"

        self.telegram_bot.send_message(report)

    def _send_children_list(self, chat_id: int):
        """List connected devices"""
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

    def _handle_chat_start(self, user_id: int, username: str, chat_id: int):
        """Show model selection menu - NO EMOJIS"""
        msg = "Select AI Model:\n\n"
        msg += "1. Trinity Large (General)\n"
        msg += "2. Deepseek 3.1 8B (Fast)\n"
        msg += "3. nvidia 7B (Fast)\n"
        msg += "4. Qwen 7B (Multilingual)\n"
        msg += "5. nvidei Flash Lite (Fast)\n"
        msg += "6. nvidei Flash (General)\n"
        msg += "7. google 70B (Advanced)\n\n"
        msg += "Reply: 1-7"

        self.telegram_bot.send_message_to_chat(chat_id, msg)
        log.info("Chat start menu shown: @%s", username)

    def _handle_model_selection(self, model_num: int, user_id: int, username: str, chat_id: int):
        """Process model selection (1-7)"""
        from sai.SaiOpenRouterClient import SaiOpenRouterClient

        client = SaiOpenRouterClient("")
        model_id = client.get_model_by_number(model_num)
        model_info = client.get_available_models().get(model_num)

        if not model_id:
            self.telegram_bot.send_message_to_chat(chat_id, "Invalid selection (1-7)")
            return

        log.info("Chat start: @%s selected %s", username, model_info["name"])

        # Publish event - let chat orchestrator check if session exists
        self.bus.publish("chat.start_request", {
            "user_id": user_id,
            "username": username,
            "model": model_id,
            "model_name": model_info["name"],
            "chat_id": chat_id
        })

        # Send simple confirmation
        self.telegram_bot.send_message_to_chat(
            chat_id,
            f"Starting: {model_info['name']}\nType your message..."
        )

    def _handle_chat_end(self, user_id: int, username: str, chat_id: int):
        """End chat session"""
        log.info("Chat end: @%s", username)
        self.bus.publish("chat.end_request", {
            "user_id": user_id,
            "username": username,
            "chat_id": chat_id
        })

    def _handle_chat_status(self, chat_id: int):
        """Chat status"""
        self.bus.publish("chat.status_request", {
            "chat_id": chat_id
        })

    def _handle_chat_help(self, chat_id: int):
        """Help message"""
        msg = """Chat Commands:
/chat_start    Begin conversation
/chat_end      End session
/chat_status   Session info
/chat_help     This message

Brain Commands:
/status        Show status
/children      List devices
/hello         Greet"""

        self.telegram_bot.send_message_to_chat(chat_id, msg)
