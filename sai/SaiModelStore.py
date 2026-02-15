from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("ModelStore")


class SaiModelStore(AraService):
    """
    Phase 5 — Manages AI model definitions and lifecycle.
    Stores static model IDs for OpenRouter and local models.
    """

    # --- Static Model Definitions ---
    
    # Vision Model (Multimodal)
    MODEL_VISION = "google/gemini-2.0-flash-lite-preview-02-05:free"
    MODEL_FREE_SEARCH = "openrouter/free"

    # Chat Models
    MODEL_TRINITY = "arcee-ai/trinity-large-preview:free"
    MODEL_GEMINI_FLASH = "nvidia/nemotron-nano-12b-v2-vl:free"
    MODEL_QWEN_NEXT = "qwen/qwen3-next-80b-a3b-instruct:free"

    # Model Registry
    MODELS = {
        1: {
            "id": MODEL_TRINITY,
            "name": "Trinity Large",
            "category": "General"
        },
        2: {
            "id": "deepseek/deepseek-r1-0528:free",
            "name": "Deepseek",
            "category": "Fast"
        },
        3: {
            "id": "nvidia/nemotron-3-nano-30b-a3b:free",
            "name": "NVIDIA: Nemotron 3 Nano",
            "category": "Fast"
        },
        4: {
            "id": "qwen/qwen3-coder:free",
            "name": "Qwen 7B",
            "category": "code"
        },
        5: {
            "id": MODEL_GEMINI_FLASH,
            "name": "Gemini Flash Lite",
            "category": "Fast"
        },
        6: {
            "id": MODEL_QWEN_NEXT,
            "name": "Qwen Next 80B",
            "category": "General"
        },
        7: {
            "id": "google/gemma-3n-e4b-it:free",
            "name": "Gemma 3N",
            "category": "Advanced"
        }
    }

    def __init__(self):
        self._status = "stopped"
        self._model = None
        self._model_name = None

    def start(self):
        self._status = "running"
        log.info("Started (Model Registry Ready).")

    def stop(self):
        self._model = None
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def get_model_id(self, key: int) -> str:
        """Get model ID by number key"""
        return self.MODELS.get(key, {}).get("id")

    def get_all_models(self) -> dict:
        """Return all available models"""
        return self.MODELS

    def load_model(self, model_name: str):
        """
        Stub — will load CoreML model from disk.
        model_name: e.g. "yolov8n" for YOLOv8 Nano
        """
        log.info("load_model('%s') called — stub, not implemented.", model_name)
        self._model_name = model_name

    def predict(self, frame_data) -> dict:
        """
        Stub — returns None. Real version runs model inference.
        """
        if self._model is None:
            log.debug("predict() called but no model loaded.")
            return None
        return None

    def is_loaded(self) -> bool:
        return self._model is not None
