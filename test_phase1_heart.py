import unittest
from unittest.mock import patch, MagicMock
import io
from brain.settings import Settings
from bus.JoBus import JoBus
from brain.brain import Brain
from telegram.MinniTelegramBot import MiniTelegramBot # Import MiniTelegramBot

class TestPhase1Heart(unittest.TestCase):

    def test_config_loads(self):
        """Test that Settings (config) can be instantiated."""
        try:
            settings = Settings()
            self.assertIsInstance(settings, Settings)
            # Optionally, check if some expected settings are present
            self.assertIsNotNone(settings.TELEGRAM_TOKEN)
            self.assertIsNotNone(settings.TELEGRAM_CHAT_ID)
            print("✅ Config loads: Settings instantiated successfully.")
        except Exception as e:
            self.fail(f"❌ Config loads failed: {e}")

    def test_jobus_running(self):
        """Test that JoBus can be instantiated."""
        try:
            bus = JoBus()
            self.assertIsInstance(bus, JoBus)
            print("✅ JoBus running: JoBus instantiated successfully.")
        except Exception as e:
            self.fail(f"❌ JoBus running failed: {e}")

if __name__ == '__main__':
    unittest.main()
