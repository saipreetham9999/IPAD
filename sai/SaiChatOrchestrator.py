"""
SaiChatOrchestrator.py - Windows Compatible (No Emoji)
Fixed for Windows cp1252 encoding issue
"""

import os
import re
from typing import Dict, Optional
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("ChatOrchestrator")


class SaiChatOrchestrator(AraService):
    """
    Main chat coordinator:
    1. Listens for telegram.chat_message on bus
    2. Routes to ChatSessionManager
    3. Calls OpenRouterClient
    4. Sends response back via Telegram
    5. Auto-cleanup via periodic signals
    """

    def __init__(self, bus, session_manager, openrouter_client, telegram_bot, settings):
        """
        Initialize orchestrator

        Args:
            bus: JoBus instance
            session_manager: SaiChatSessionManager
            openrouter_client: SaiOpenRouterClient
            telegram_bot: MiniTelegramBot (to send replies)
            settings: Settings instance (has TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        """
        self.bus = bus
        self.session_manager = session_manager
        self.openrouter_client = openrouter_client
        self.telegram_bot = telegram_bot
        self.settings = settings
        self._status = "stopped"

        # System prompt for all chats
        self.system_prompt = """You are a helpful AI assistant integrated into a home security Brain.
You provide helpful, friendly responses. Keep answers concise.
You can help with questions, give advice, and have natural conversations."""

    def start(self):
        """Start listening for chat messages"""
        self._status = "running"

        # Listen for chat-related events
        self.bus.subscribe("telegram.chat_message", self._on_chat_message)
        self.bus.subscribe("chat.start_request", self._on_start_chat)
        self.bus.subscribe("chat.end_request", self._on_end_chat)
        self.bus.subscribe("chat.status_request", self._on_status_request)

        # Periodic cleanup (bus can trigger this)
        self.bus.subscribe("chat.cleanup", self._on_cleanup)

        log.info("Started. Listening for chat messages.")

    def stop(self):
        """Stop service"""
        self._status = "stopped"
        log.info("Stopped.")

    def status(self) -> str:
        return self._status

    # ========================================================================
    # Event handlers (bus subscriptions)
    # ========================================================================

    def _on_chat_message(self, data: dict):
        """
        Handle incoming chat message from Telegram

        Expected data:
        {
            "user_id": 123,
            "username": "john_doe",
            "message": "What is the weather?",
            "chat_id": 456  # Telegram group/user chat ID
        }
        """
        user_id = data.get("user_id")
        username = data.get("username")
        message = data.get("message")
        chat_id = data.get("chat_id")

        if not all([user_id, message, chat_id]):
            log.warning("Invalid chat message data: %s", data)
            return

        # Get session - if none exists, this is first message
        session = self.session_manager.get_session(user_id)

        if not session:
            # No session - show welcome/help message
            log.info("First message from @%s - no session yet", username)
            self._show_welcome(user_id, username, chat_id)
            return

        # Session exists - process message
        self._process_chat_message(user_id, username, message, chat_id)

    def _on_start_chat(self, data: dict):
        """
        Handle chat start request

        Expected data:
        {
            "user_id": 123,
            "username": "john_doe",
            "model": "mistral",  # optional, defaults to mistral
            "chat_id": 456
        }
        """
        user_id = data.get("user_id")
        username = data.get("username")
        model = data.get("model", "mistralai/mistral-7b-instruct:free")
        chat_id = data.get("chat_id")

        if not all([user_id, username, chat_id]):
            log.warning("Invalid start chat data: %s", data)
            return

        # Try to start session
        session = self.session_manager.start_session(user_id, username, model)

        if not session:
            reply = "Chat unavailable - too many users. Try again later."
            self._send_reply(chat_id, reply)
            return

        reply = """Chat started!

Model: Mistral 7B
Available models: mistral, llama, qwen

You can now:
- Ask any question
- Have a conversation
- Get help with tasks

Send /chat_end to stop chatting"""
        self._send_reply(chat_id, reply)

    def _on_end_chat(self, data: dict):
        """Handle chat end request"""
        user_id = data.get("user_id")
        chat_id = data.get("chat_id")

        if self.session_manager.end_session(user_id):
            reply = "Chat ended.\n\nSend any message to start a new conversation."
            self._send_reply(chat_id, reply)
        else:
            reply = "No active chat session."
            self._send_reply(chat_id, reply)

    def _on_status_request(self, data: dict):
        """Handle status/stats request"""
        chat_id = data.get("chat_id")
        stats = self.session_manager.get_stats()

        reply = f"""Chat System Status:
Active Sessions: {stats['active_sessions']}/{stats['max_capacity']}
Usage: {stats['usage_percent']}%
Idle Timeout: {stats['idle_timeout_minutes']:.0f} minutes

Available AI Models:
- Mistral 7B (default)
- Llama 3 8B
- Qwen 7B

All models are free to use!"""

        self._send_reply(chat_id, reply)

    def _on_cleanup(self, data: dict):
        """Handle periodic cleanup signal"""
        removed = self.session_manager.cleanup_expired()
        if removed > 0:
            log.info("Cleanup: removed %d expired sessions", removed)

    # ========================================================================
    # Core chat processing
    # ========================================================================

    def _show_welcome(self, user_id: int, username: str, chat_id: int):
        """
        Show welcome message with options when user sends first message
        """
        reply = """Hi!

Welcome to Brain Chat!

I'm an AI assistant here to help you with:
- Questions and answers
- Advice and suggestions
- General conversation
- Problem solving

To start chatting, reply:
/chat_start

Then just type your question!

Other commands:
/chat_status  - Show system status
/chat_help    - Show chat help

Type /chat_start to begin!"""

        self._send_reply(chat_id, reply)

    def _process_chat_message(self, user_id: int, username: str, message: str, chat_id: int):
        """
        Process chat message for active session
        1. Add to session history
        2. Call OpenRouter API
        3. Send response back
        4. Track tokens
        """
        session = self.session_manager.get_session(user_id)
        if not session:
            log.error("Session disappeared for user %d", user_id)
            return

        log.info("Processing chat for @%s: %d chars", username, len(message))

        # Add user message to history
        self.session_manager.add_message(user_id, "user", message)

        # Build messages for API (system prompt + history)
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        messages.extend(session.get_context())

        # Show typing indicator
        self._send_reply(chat_id, "Thinking...")

        # Call OpenRouter
        result = self.openrouter_client.send_message(
            messages=messages,
            model=session.model,
            temperature=0.7,
            max_tokens=500
        )

        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            reply = f"Error: {error_msg}"
            log.error("OpenRouter error: %s", error_msg)
            self._send_reply(chat_id, reply)
            return

        # Add AI response to history
        ai_response = result["response"]
        tokens = result.get("tokens_used", 0)
        self.session_manager.add_message(user_id, "assistant", ai_response, tokens)

        # Send response back
        log.info(
            "Chat response for @%s: %d tokens, %d chars",
            username, tokens, len(ai_response)
        )
        self._send_reply(chat_id, ai_response)



    def _send_reply(self, chat_id: int, text: str):
        """Send reply via Telegram using telegram_bot"""
        if not chat_id:
            log.warning("No chat_id provided for reply")
            return

        # Reuse telegram_bot's send method (handles retries, errors, etc)
        self.telegram_bot.send_message_to_chat(chat_id, text)
        log.debug("Reply queued to chat %d", chat_id)