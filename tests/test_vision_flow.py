import time
import logging
import sys
import os

# Add project root to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bus.JoBus import JoBus
from sai.SaiVisionEngine import SaiVisionEngine

# Configure logging to show up in console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_vision_flow():
    print(">>> 1. Initializing Bus...")
    bus = JoBus()

    print(">>> 2. Initializing Vision Engine...")
    # We don't need real tier_manager or alert_rules for this test
    vision_engine = SaiVisionEngine(bus=bus)

    print(">>> 3. Starting Vision Engine...")
    vision_engine.start()

    # Give it a second to subscribe
    time.sleep(0.5)

    print(">>> 4. Constructing Mock Payload...")
    # A tiny valid base64 jpeg (1x1 pixel white)
    dummy_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVjaFGW1iZ2lqa3Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q=="
    
    payload = {
        "device_name": "TestCamera01",
        "type": "frame",
        "data": dummy_base64,
        "timestamp": time.time()
    }

    print(f">>> 5. Publishing 'child.report.received' event with payload keys: {list(payload.keys())}")
    bus.publish("child.report.received", payload)

    print(">>> 6. Waiting for processing (5 seconds)...")
    time.sleep(5)

    print(">>> 7. Stopping Engine...")
    vision_engine.stop()
    print(">>> Test Complete. Check logs above for 'VisionEngine' output.")

if __name__ == "__main__":
    test_vision_flow()
