import os


class Settings:
    def __init__(self):
        self.TELEGRAM_TOKEN = "7981227869:AAFqe9uj5wWMQWRPT0qk11WWh0G7pceeABk"
        self.BRAIN_NAME = "ARA-BRAIN"
        self.OPENROUTER_API_KEY =""

    def _require(self, key: str):
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return value
