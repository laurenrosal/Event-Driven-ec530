import json
import uuid
from datetime import datetime, timezone
from Messaging.broker import Broker
from Messaging.topics import (
    IMAGE_SUBMITTED,
    IMAGE_RECEIVED,
    IMAGE_VALIDATED,
    IMAGE_INVALID,
    IMAGE_PROCESSING,
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def is_valid_image(path: str) -> bool:
    import os
    _, ext = os.path.splitext(path)
    return ext.lower() in ALLOWED_EXTENSIONS

def handle_image_submitted(message):
    """Handles incoming image.submitted events."""
    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})
        image_id = payload.get("image_id")
        batch_id = payload.get("batch_id")
        path = payload.get("path")

        print(f"\n[Upload Service] Received image: {image_id} from batch: {batch_id}")

        broker = Broker()

        # Step 1 — publish image.received
        broker.publish(IMAGE_RECEIVED, {
            "type": "publish",
            "topic": IMAGE_RECEIVED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Upload Service] image.received published for: {image_id}")

        # Step 2 — validate file type
        if not is_valid_image(path):
            broker.publish(IMAGE_INVALID, {
                "type": "publish",
                "topic": IMAGE_INVALID,
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "payload": {
                    "image_id": image_id,
                    "batch_id": batch_id,
                    "path": path,
                    "reason": "Invalid file type",
                    "timestamp": get_timestamp()
                }
            })
            print(f"[Upload Service] image.invalid published for: {image_id}")
            return

        # Step 3 — publish image.validated
        broker.publish(IMAGE_VALIDATED, {
            "type": "publish",
            "topic": IMAGE_VALIDATED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Upload Service] image.validated published for: {image_id}")

        # Step 4 — hand off to image processing
        broker.publish(IMAGE_PROCESSING, {
            "type": "publish",
            "topic": IMAGE_PROCESSING,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Upload Service] image.processing published for: {image_id}")

    except Exception as e:
        print(f"[Upload Service] ERROR: {e}")

def main():
    broker = Broker()
    print("[Upload Service] Starting up...")
    print("[Upload Service] Listening for image.submitted events...\n")
    broker.subscribe(IMAGE_SUBMITTED, handle_image_submitted)
    broker.listen()

if __name__ == "__main__":
    main()