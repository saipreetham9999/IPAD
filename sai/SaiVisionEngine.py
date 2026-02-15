from core.AraService import AraService
from bus.JoLogger import get_logger
from sai.SaiOpenRouterClient import SaiOpenRouterClient
from sai.SaiModelStore import SaiModelStore
from brain.settings import Settings

log = get_logger("VisionEngine")

# Decision object shape — always returned from process_frame()
EMPTY_DECISION = {
    "person_present": False,
    "count": 0,
    "zone": None,
    "motion_level": 0.0,
    "anomaly": False,
    "confidence": 0.0,
    "processed_by": "none",
}


class SaiVisionEngine(AraService):
    """
    Phase 5 — Vision Engine
    Processes camera frames from children.
    If a frame is present, it sends it to an AI model (OpenRouter) for analysis.
    If the AI detects something interesting, it publishes an alert.
    """

    def __init__(self, bus, tier_manager=None, alert_rules=None):
        self.bus = bus
        self.tier_manager = tier_manager
        self.alert_rules = alert_rules
        self._status = "stopped"
        self.settings = Settings()
        
        # Initialize OpenRouter client for vision
        # We'll use a vision-capable model
        self.ai_client = SaiOpenRouterClient(self.settings.OPENROUTER_API_KEY)
        
        # Vision model to use (must support image input)
        # Using Gemini Flash Lite or Qwen VL if available, otherwise falling back to text description
        # For now, we will use a model known to handle images if possible, or just text prompt
        self.vision_model = SaiModelStore.MODEL_VISION

    def start(self):
        self._status = "running"
        self.bus.subscribe("child.report.received", self._on_report)
        log.info("Started Vision Engine.")

    def stop(self):
        self._status = "stopped"
        if self.ai_client:
            self.ai_client.close()
        log.info("Stopped.")

    def status(self):
        return self._status

    def _on_report(self, data: dict):
        """
        Called when a child sends a report.
        Checks for 'frame' data (base64 encoded image).
        """
        log.info("Received report from child.")
        device = data.get("device_name", "unknown")
        report_type = data.get("type", "unknown")
        frame_type = data.get("frame_type", "unknown")
        
        # Only process if it's a frame report and has data
        if report_type == "frame" and "data" in data:
            log.info("Processing frame from %s...", device)
            self._analyze_frame(device, data["data"])
        else:
            log.debug("Report from '%s' ignored (no frame data).", device)

    def _analyze_frame(self, device: str, jpeg_image: str):
        """
        Sends the image to the AI model for analysis.
        """
        # Prepare the prompt
        prompt = """You are a security camera AI. 
        1. Analyze this image briefly in 3 lines max.
        2. If you see a person, fire, weapon, or immediate danger, and your response with the exact word: GAYATHRI.
        3. If everything is safe/normal, do NOT use that word.
        """
        
        # Construct the message payload for OpenRouter (multimodal)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{jpeg_image}"
                        }
                    }
                ]
            }
        ]

        # Send to AI
        log.info("Sending frame to AI model (%s)...", self.vision_model)
        result = self.ai_client.send_message(
            messages=messages,
            model=self.vision_model,
            max_tokens=150
        )

        if result["success"]:
            description = result["response"]
            log.info("AI Analysis for %s: %s", device, description)
            
            # Check for alert keyword
            is_alert = "GAYATHRI" in description
            log.info("Is alert? %s", is_alert)
            
            # Clean up the description (remove the keyword if present so it looks cleaner)
            clean_description = description.replace("GAYATHRI", "").strip()

            if is_alert:

                self.bus.publish("vision.analysis.result", {
                    "device": device,
                    "description": f"⚠️ ALERT: {clean_description}",
                    "image_data": jpeg_image
                })

                self.bus.publish("alert.triggered", {
                    "source": f"Vision ({device})",
                    "message": f"CRITICAL: {clean_description}"
                })
            else:
                # Normal update - just send photo + description
                self.bus.publish("vision.analysis.result", {
                    "device": device,
                    "description": clean_description,
                    "image_data": jpeg_image
                })

        else:
            log.error("AI Vision failed: %s", result["error"])

    def process_frame(self, frame_data) -> dict:
        """
        Legacy stub - kept for compatibility if needed.
        """
        return dict(EMPTY_DECISION)
