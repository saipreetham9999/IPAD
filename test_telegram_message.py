from brain.settings import Settings
from bus.jo_bus import JoBus
from telegram.mini_telegram_bot import MiniTelegramBot
import os

# Ensure environment variables are set for testing
# You might need to set these in your environment or replace with actual values for testing
# os.environ["TELEGRAM_TOKEN"] = "YOUR_TELEGRAM_BOT_TOKEN"
# os.environ["TELEGRAM_CHAT_ID"] = "YOUR_TELEGRAM_CHAT_ID"

def test_send_telegram_message():
    print("--- Running Telegram Message Test ---")

    # 1. Instantiate Settings
    settings = Settings()

    # 2. Instantiate JoBus (can be a mock if not relevant for this specific test)
    bus = JoBus()

    # 3. Instantiate MiniTelegramBot
    telegram_bot = MiniTelegramBot(settings=settings, bus=bus)

    # 4. Define a test message
    test_message = "Hello from your Python project! This is a test message."

    # 5. Send the message
    try:
        telegram_bot._send_message_worker(test_message)
        print(f"Successfully sent message: '{test_message}'")
    except Exception as e:
        print(f"Failed to send message: {e}")

    print("--- Telegram Message Test Finished ---")

if __name__ == "__main__":
    # You might need to manually set the token and chat_id here for local testing
    # if you're not using environment variables or if the default values in settings.py are not valid.
    # Example:
    # os.environ["TELEGRAM_TOKEN"] = "7981227869:AAFqe9uj5wWMQWRPT0qk11WWh0G7pceeABk"
    # os.environ["TELEGRAM_CHAT_ID"] = "7228944872"

    test_send_telegram_message()
