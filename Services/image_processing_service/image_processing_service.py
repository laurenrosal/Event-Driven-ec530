import json
import uuid
import time
from datetime import datetime, timezone
from Messaging.broker import Broker
from Messaging.topics import (
    IMAGE_PROCESSING,
    IMAGE_PROCESSING_COMPLETE,
    ANNOTATION_STORING,
    IMAGE_FAILED
)

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def simulate_processing(image_id: str) -> dict:
    """
    Simulated image processing.
    Replace this with real processing logic later.
    """
    time.sleep(1)  # simulate processing time
    return {
        "image_id": image_id,
        "width": 1920,
        "height": 1080,
        "format": "JPEG",
        "processed": True
    }

def handle_image_processing(message):
    """Handles incoming image.processing events."""
    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})
        image_id = payload.get("image_id")
        batch_id = payload.get("batch_id")
        path = payload.get("path")

        print(f"\n[Image Processing] Processing image: {image_id}")

        broker = Broker()

        # Step 1 — simulate processing
        result = simulate_processing(image_id)
        print(f"[Image Processing] Done processing: {image_id}")

        # Step 2 — publish image.processing.complete
        broker.publish(IMAGE_PROCESSING_COMPLETE, {
            "type": "publish",
            "topic": IMAGE_PROCESSING_COMPLETE,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "result": result,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Image Processing] image.processing.complete published for: {image_id}")

        # Step 3 — hand off to annotation storing (document DB)
        broker.publish(ANNOTATION_STORING, {
            "type": "publish",
            "topic": ANNOTATION_STORING,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Image Processing] annotation.storing published for: {image_id}")

    except Exception as e:
        print(f"[Image Processing] ERROR: {e}")
        broker = Broker()
        broker.publish(IMAGE_FAILED, {
            "type": "publish",
            "topic": IMAGE_FAILED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "reason": str(e),
                "timestamp": get_timestamp()
            }
        })

def main():
    broker = Broker()
    print("[Image Processing] Starting up...")
    print("[Image Processing] Listening for image.processing events...\n")
    broker.subscribe(IMAGE_PROCESSING, handle_image_processing)
    broker.listen()

if __name__ == "__main__":
    main()