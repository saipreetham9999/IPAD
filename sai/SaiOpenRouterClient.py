"""
SaiOpenRouterClient.py
OpenRouter API client using requests (no extra dependencies)
"""

import requests
import json
from typing import Dict, List, Optional
from bus.JoLogger import get_logger
from sai.SaiModelStore import SaiModelStore

log = get_logger("OpenRouterClient")

class SaiOpenRouterClient:
    """Low-level OpenRouter API wrapper"""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        if not api_key:
            log.warning("OpenRouter API key is empty")

    def send_message(
        self,
        messages: List[Dict],
        model: str = SaiModelStore.MODEL_TRINITY,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict:
        """Send message to OpenRouter"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://brain-ai.local",
            "X-Title": "Brain Chat"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9
        }

        try:
            response = self.session.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            log.info("OpenRouter request sent")
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"].get("message", error_msg)
                except:
                    pass

                log.error("OpenRouter error: %s", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "response": None,
                    "tokens_used": 0,
                    "model": model
                }

            data = response.json()

            if "choices" not in data or len(data["choices"]) == 0:
                log.error("No response from model")
                return {
                    "success": False,
                    "error": "No response from model",
                    "response": None,
                    "tokens_used": 0,
                    "model": model
                }

            ai_message = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)

            return {
                "success": True,
                "response": ai_message,
                "tokens_used": tokens_used,
                "model": model,
                "error": None
            }

        except requests.exceptions.Timeout:
            log.error("OpenRouter timeout")
            return {
                "success": False,
                "error": "Request timeout",
                "response": None,
                "tokens_used": 0,
                "model": model
            }

        except requests.exceptions.ConnectionError as e:
            log.error("OpenRouter connection error")
            return {
                "success": False,
                "error": "Network error",
                "response": None,
                "tokens_used": 0,
                "model": model
            }

        except Exception as e:
            log.error("Unexpected error: %s", type(e).__name__)
            return {
                "success": False,
                "error": f"Error: {type(e).__name__}",
                "response": None,
                "tokens_used": 0,
                "model": model
            }

    def get_available_models(self) -> Dict:
        return SaiModelStore.MODELS.copy()

    def get_model_by_number(self, number: int) -> Optional[str]:
        if number in SaiModelStore.MODELS:
            return SaiModelStore.MODELS[number]["id"]
        return None

    def close(self):
        self.session.close()
