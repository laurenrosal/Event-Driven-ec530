import json
import uuid
import time
from datetime import datetime, timezone
from Messaging.broker import Broker
from Messaging.topics import (
    ANNOTATION_STORING,
    ANNOTATION_STORED,
    IMAGE_ANNOTATING,
    IMAGE_ANNOTATED,
    EMBEDDING_PROCESSING,
    ANNOTATION_FAILED
)

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def simulate_annotation(image_id: str) -> dict:
    """
    Simulated annotation.
    Replace this with real annotation logic later.
    """
    time.sleep(1)  # simulate annotation time
    return {
        "image_id": image_id,
        "objects": [
            {"label": "cat", "confidence": 0.95, "bbox": [10, 20, 100, 200]},
            {"label": "couch", "confidence": 0.88, "bbox": [0, 150, 300, 400]}
        ],
        "annotated_at": get_timestamp()
    }

def handle_annotation_storing(message):
    """Handles incoming annotation.storing events."""
    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})
        image_id = payload.get("image_id")
        batch_id = payload.get("batch_id")
        path = payload.get("path")

        print(f"\n[Annotation Service] Received image: {image_id}")

        broker = Broker()

        # Step 1 — publish image.annotating
        broker.publish(IMAGE_ANNOTATING, {
            "type": "publish",
            "topic": IMAGE_ANNOTATING,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Annotation Service] image.annotating published for: {image_id}")

        # Step 2 — simulate annotation
        annotation = simulate_annotation(image_id)
        print(f"[Annotation Service] Annotation complete for: {image_id}")
        print(f"[Annotation Service] Found {len(annotation['objects'])} objects")

        # Step 3 — publish annotation.storing (saving to document DB)
        broker.publish(ANNOTATION_STORED, {
            "type": "publish",
            "topic": ANNOTATION_STORED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "annotation": annotation,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Annotation Service] annotation.stored published for: {image_id}")

        # Step 4 — publish image.annotated
        broker.publish(IMAGE_ANNOTATED, {
            "type": "publish",
            "topic": IMAGE_ANNOTATED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Annotation Service] image.annotated published for: {image_id}")

        # Step 5 — hand off to embedding service
        broker.publish(EMBEDDING_PROCESSING, {
            "type": "publish",
            "topic": EMBEDDING_PROCESSING,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "annotation": annotation,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Annotation Service] embedding.processing published for: {image_id}")

    except Exception as e:
        print(f"[Annotation Service] ERROR: {e}")
        broker = Broker()
        broker.publish(ANNOTATION_FAILED, {
            "type": "publish",
            "topic": ANNOTATION_FAILED,
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
    print("[Annotation Service] Starting up...")
    print("[Annotation Service] Listening for annotation.storing events...\n")
    broker.subscribe(ANNOTATION_STORING, handle_annotation_storing)
    broker.listen()

if __name__ == "__main__":
    main()