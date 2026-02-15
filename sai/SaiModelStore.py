from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("ModelStore")


class SaiModelStore(AraService):
    """
    Stub for Phase 5 — manages AI model loading and lifecycle.
    Will load YOLOv8 Nano when CoreML is available on iPad.
    """

    def __init__(self):
        self._status = "stopped"
        self._model = None
        self._model_name = None

    def start(self):
        self._status = "running"
        log.info("Started (stub — no model loaded).")

    def stop(self):
        self._model = None
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def load_model(self, model_name: str):
        """
        Stub — will load CoreML model from disk.
        model_name: e.g. "yolov8n" for YOLOv8 Nano
        """
        log.info("load_model('%s') called — stub, not implemented.", model_name)
        self._model_name = model_name
        # Real implementation:
        #   self._model = coreml.load(f"models/{model_name}.mlmodel")

    def predict(self, frame_data) -> dict:
        """
        Stub — returns None. Real version runs model inference.
        """
        if self._model is None:
            log.debug("predict() called but no model loaded.")
            return None
        # Real implementation:
        #   return self._model.predict(frame_data)
        return None

    def is_loaded(self) -> bool:
        return self._model is not None
