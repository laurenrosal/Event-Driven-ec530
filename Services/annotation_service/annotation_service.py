import json
import uuid
from datetime import datetime, timezone

from Messaging.broker import Broker
from databases.document_db.document_db import DocumentDB
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

def handle_annotation_storing(message):
    image_id = None
    batch_id = None

    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})

        image_id = payload.get("image_id")
        batch_id = payload.get("batch_id")
        path = payload.get("path")
        annotation = payload.get("annotation", {})

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

        # Step 2 — store real annotation JSON in MongoDB
        db = DocumentDB()
        db.store_annotation(
            image_id=image_id,
            batch_id=batch_id,
            path=path,
            annotation=annotation
        )
        print(f"[Annotation Service] Stored annotation in MongoDB for: {image_id}")

        # Step 3 — publish annotation.stored
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
                "path": path,
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
                "path": path,
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