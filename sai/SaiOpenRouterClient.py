"""
SaiOpenRouterClient.py
OpenRouter API client using requests (no extra dependencies)
Part of Phase 5 — AI layer
"""

import requests
import json
from typing import Dict, List, Optional
from bus.JoLogger import get_logger

log = get_logger("OpenRouterClient")

class SaiOpenRouterClient:
    """
    Low-level OpenRouter API wrapper
    Handles all HTTP calls to OpenRouter
    """
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Free models available on OpenRouter (no credit needed for testing)
    FREE_MODELS = {
        "mistral": "arcee-ai/trinity-large-preview:free",
        "llama": "meta-llama/llama-3-8b-instruct:free",
        "qwen": "qwen/qwen-7b-chat:free",
    }
    
    def __init__(self, api_key: str):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        
        if not api_key:
            log.warning("OpenRouter API key is empty")
    
    def send_message(
        self,
        messages: List[Dict],
        model: str = "mistralai/mistral-7b:free",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict:
        """
        Send message to OpenRouter and get response
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            model: Model identifier (see FREE_MODELS)
            temperature: 0.0-2.0 (higher = more creative)
            max_tokens: Max response length
        
        Returns:
            {
                "success": bool,
                "response": str,        # AI's reply
                "tokens_used": int,
                "model": str,
                "error": str           # If failed
            }
        """
        
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
            log.debug(
                "Calling OpenRouter: model=%s, messages=%d, tokens=%d",
                model, len(messages), max_tokens
            )
            
            response = self.session.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"].get("message", error_msg)
                except:
                    pass
                
                log.error("OpenRouter API error: %s", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "response": None,
                    "tokens_used": 0,
                    "model": model
                }
            
            data = response.json()
            
            # Validate response structure
            if "choices" not in data or len(data["choices"]) == 0:
                log.error("Invalid response from OpenRouter: no choices")
                return {
                    "success": False,
                    "error": "No response from model",
                    "response": None,
                    "tokens_used": 0,
                    "model": model
                }
            
            # Extract message
            ai_message = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            
            log.debug("OpenRouter response: %d tokens, %d chars", 
                     tokens_used, len(ai_message))
            
            return {
                "success": True,
                "response": ai_message,
                "tokens_used": tokens_used,
                "model": model,
                "error": None
            }
        
        except requests.exceptions.Timeout:
            log.error("OpenRouter request timeout (30s)")
            return {
                "success": False,
                "error": "Request timeout - OpenRouter not responding",
                "response": None,
                "tokens_used": 0,
                "model": model
            }
        
        except requests.exceptions.ConnectionError as e:
            log.error("OpenRouter connection error: %s", e)
            return {
                "success": False,
                "error": "Network error - cannot reach OpenRouter",
                "response": None,
                "tokens_used": 0,
                "model": model
            }
        
        except json.JSONDecodeError:
            log.error("Invalid JSON response from OpenRouter")
            return {
                "success": False,
                "error": "Invalid response format from OpenRouter",
                "response": None,
                "tokens_used": 0,
                "model": model
            }
        
        except Exception as e:
            log.error("Unexpected OpenRouter error: %s", type(e).__name__)
            return {
                "success": False,
                "error": f"Unexpected error: {type(e).__name__}",
                "response": None,
                "tokens_used": 0,
                "model": model
            }
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of available free models"""
        return self.FREE_MODELS.copy()
    
    def close(self):
        """Close HTTP session"""
        self.session.close()
        log.debug("Session closed")
