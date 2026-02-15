"""
UserPreferences.py
Store user model preferences locally
"""

import json
import os
from typing import Optional
from bus.JoLogger import get_logger

log = get_logger("UserPreferences")

class UserPreferences:
    """Store and retrieve user preferences"""

    PREFS_FILE = "data/user_preferences.json"

    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        """Create preferences file if missing"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.PREFS_FILE):
            with open(self.PREFS_FILE, "w") as f:
                json.dump({}, f)

    def get_preferred_model(self, user_id: int) -> Optional[int]:
        """Get user's preferred model number (1-7)"""
        try:
            with open(self.PREFS_FILE, "r") as f:
                prefs = json.load(f)

            if str(user_id) in prefs:
                model_num = prefs[str(user_id)].get("model_number")
                if 1 <= model_num <= 7:
                    return model_num
        except Exception as e:
            log.error("Error reading preferences: %s", type(e).__name__)

        return None

    def set_preferred_model(self, user_id: int, model_number: int):
        """Save user's preferred model (1-7)"""
        if not (1 <= model_number <= 7):
            log.warning("Invalid model number: %d", model_number)
            return False

        try:
            with open(self.PREFS_FILE, "r") as f:
                prefs = json.load(f)

            prefs[str(user_id)] = {"model_number": model_number}

            with open(self.PREFS_FILE, "w") as f:
                json.dump(prefs, f, indent=2)

            log.info("Saved model preference for user %d: %d", user_id, model_number)
            return True

        except Exception as e:
            log.error("Error saving preferences: %s", type(e).__name__)
            return False

    def clear_preference(self, user_id: int):
        """Clear user's saved model preference"""
        try:
            with open(self.PREFS_FILE, "r") as f:
                prefs = json.load(f)

            if str(user_id) in prefs:
                del prefs[str(user_id)]

            with open(self.PREFS_FILE, "w") as f:
                json.dump(prefs, f, indent=2)

            log.info("Cleared preference for user %d", user_id)

        except Exception as e:
            log.error("Error clearing preferences: %s", type(e).__name__)
