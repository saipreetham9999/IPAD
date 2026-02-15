"""
SaiChatSessionManager.py
Manages multi-user chat sessions with 30min auto-cleanup
Part of Phase 5 — AI layer
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Lock
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("ChatSessionManager")


class ChatSession:
    """Single conversation between user and AI"""
    
    def __init__(self, user_id: int, username: str, model: str, max_history: int = 10):
        self.user_id = user_id
        self.username = username
        self.model = model
        self.max_history = max_history  # Keep last N messages
        
        self.messages: List[Dict] = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.is_active = True
        self.total_tokens_used = 0
    
    def add_message(self, role: str, content: str, tokens: int = 0):
        """Add message to history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now()
        self.total_tokens_used += tokens
        
        # Keep only last N messages to save memory
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_context(self) -> List[Dict]:
        """Get messages for API (without timestamps)"""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self.messages
        ]
    
    def is_expired(self, timeout_seconds: int = 1800) -> bool:
        """Check if session exceeded idle timeout (30min default)"""
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed > timeout_seconds
    
    def duration_minutes(self) -> float:
        """Total time session has been open"""
        elapsed = datetime.now() - self.created_at
        return elapsed.total_seconds() / 60
    
    def message_count(self) -> int:
        """Number of messages in this session"""
        return len(self.messages)
    
    def to_dict(self) -> Dict:
        """Export session info"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "model": self.model,
            "messages": self.message_count(),
            "duration_minutes": round(self.duration_minutes(), 1),
            "tokens_used": self.total_tokens_used,
            "last_activity": self.last_activity.isoformat()
        }


class SaiChatSessionManager(AraService):
    """
    Manages multiple chat sessions
    - Creates/destroys per-user conversations
    - Auto-cleanup after 30min inactivity
    - Thread-safe (uses Lock)
    - Max 20 concurrent users (configurable)
    """
    
    def __init__(self, bus, max_users: int = 20, idle_timeout_seconds: int = 1800):
        """
        Initialize session manager
        
        Args:
            bus: JoBus instance
            max_users: Maximum concurrent chat sessions
            idle_timeout_seconds: Timeout before auto-cleanup (1800s = 30min)
        """
        self.bus = bus
        self.max_users = max_users
        self.idle_timeout_seconds = idle_timeout_seconds
        
        self.sessions: Dict[int, ChatSession] = {}
        self.lock = Lock()
        self._status = "stopped"
    
    def start(self):
        """Start the service"""
        self._status = "running"
        self.bus.subscribe("chat.cleanup", self._on_cleanup_signal)
        log.info(
            "Started. Max users: %d, Timeout: %ds (%.1f min)",
            self.max_users,
            self.idle_timeout_seconds,
            self.idle_timeout_seconds / 60
        )
    
    def stop(self):
        """Stop the service"""
        with self.lock:
            self.sessions.clear()
        self._status = "stopped"
        log.info("Stopped.")
    
    def status(self) -> str:
        return self._status
    
    def start_session(
        self,
        user_id: int,
        username: str,
        model: str
    ) -> Optional[ChatSession]:
        """
        Create new chat session for user
        
        Args:
            user_id: Telegram user ID (unique)
            username: Telegram username
            model: Model to use (e.g. "mistralai/mistral-7b:free")
        
        Returns:
            ChatSession if created, None if max users reached
        """
        with self.lock:
            # User already has session - return existing
            if user_id in self.sessions:
                return self.sessions[user_id]
            
            # Clean expired sessions to make room
            if len(self.sessions) >= self.max_users:
                removed = self._cleanup_expired_sessions()
                if len(self.sessions) >= self.max_users:
                    log.warning(
                        "Cannot create session: max users (%d) reached",
                        self.max_users
                    )
                    return None
            
            # Create new session
            session = ChatSession(user_id, username, model)
            self.sessions[user_id] = session
            
            log.info(
                "Chat session started: @%s (user_id=%d, model=%s)",
                username, user_id, model
            )
            
            return session
    
    def get_session(self, user_id: int) -> Optional[ChatSession]:
        """Get existing session"""
        with self.lock:
            return self.sessions.get(user_id)
    
    def end_session(self, user_id: int) -> bool:
        """
        End user's chat session
        
        Returns:
            True if session existed and was deleted
        """
        with self.lock:
            if user_id in self.sessions:
                session = self.sessions[user_id]
                del self.sessions[user_id]
                log.info(
                    "Chat session ended: @%s (duration: %.1f min, messages: %d)",
                    session.username,
                    session.duration_minutes(),
                    session.message_count()
                )
                return True
        return False
    
    def add_message(
        self,
        user_id: int,
        role: str,
        content: str,
        tokens: int = 0
    ) -> bool:
        """
        Add message to session
        
        Args:
            user_id: User ID
            role: "user" or "assistant"
            content: Message text
            tokens: Tokens used in API call (for tracking)
        
        Returns:
            True if added, False if no session
        """
        session = self.get_session(user_id)
        if not session:
            return False
        
        session.add_message(role, content, tokens)
        return True
    
    def get_active_sessions(self) -> List[Dict]:
        """Get info about all active sessions"""
        with self.lock:
            return [sess.to_dict() for sess in self.sessions.values()]
    
    def get_session_count(self) -> int:
        """Number of active sessions"""
        with self.lock:
            return len(self.sessions)
    
    def get_stats(self) -> Dict:
        """Get manager statistics"""
        with self.lock:
            active = len(self.sessions)
            return {
                "active_sessions": active,
                "max_capacity": self.max_users,
                "usage_percent": round((active / self.max_users) * 100, 1),
                "idle_timeout_minutes": self.idle_timeout_seconds / 60,
                "sessions": [s.to_dict() for s in self.sessions.values()]
            }
    
    def cleanup_expired(self) -> int:
        """
        Cleanup expired sessions
        Thread-safe version
        
        Returns:
            Number of sessions removed
        """
        with self.lock:
            return self._cleanup_expired_sessions()
    
    def _cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions (must be called with lock held)
        
        Returns:
            Number removed
        """
        expired_ids = [
            uid for uid, sess in self.sessions.items()
            if sess.is_expired(self.idle_timeout_seconds)
        ]
        
        for uid in expired_ids:
            session = self.sessions[uid]
            del self.sessions[uid]
            log.info(
                "Auto-cleanup: @%s session expired (idle: %.1f min)",
                session.username,
                (datetime.now() - session.last_activity).total_seconds() / 60
            )
        
        return len(expired_ids)
    
    def _on_cleanup_signal(self, data: dict):
        """Handle cleanup signal from bus"""
        removed = self.cleanup_expired()
        if removed > 0:
            log.info("Cleanup signal processed: removed %d expired sessions", removed)
