import json
import uuid
import time
from datetime import datetime, timezone
from Messaging.broker import Broker
from databases.vector_db.vector_db import VectorDB
from Messaging.topics import (
    EMBEDDING_PROCESSING,
    EMBEDDING_COMPLETE,
    VECTOR_STORING,
    VECTOR_STORED,
    EMBEDDING_FAILED
)

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def simulate_embedding(image_id: str, annotation: dict) -> list:
    """
    Simulated embedding generation.
    Replace this with real embedding logic later.
    """
    time.sleep(1)  # simulate embedding time
    # return a fake vector of 128 dimensions
    import random
    return [round(random.uniform(-1, 1), 4) for _ in range(128)]

def handle_embedding_processing(message):
    """Handles incoming embedding.processing events."""
    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})
        image_id = payload.get("image_id")
        batch_id = payload.get("batch_id")
        annotation = payload.get("annotation", {})

        print(f"\n[Embedding Service] Received image: {image_id}")

        broker = Broker()

        # Step 1 — simulate embedding generation
        vector = simulate_embedding(image_id, annotation)
        print(f"[Embedding Service] Embedding generated for: {image_id}")
        print(f"[Embedding Service] Vector dimensions: {len(vector)}")

        # Step 2 — publish embedding.complete
        broker.publish(EMBEDDING_COMPLETE, {
            "type": "publish",
            "topic": EMBEDDING_COMPLETE,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "vector_size": len(vector),
                "timestamp": get_timestamp()
            }
        })
        print(f"[Embedding Service] embedding.complete published for: {image_id}")

        # Step 3 — publish vector.storing (sending to vector DB)
        db = VectorDB()
        db.store_vector(
            image_id=image_id,
            batch_id=batch_id,
            path=payload.get("path", ""),
            vector=vector
        )

        # Step 4 — publish vector.storing
        broker.publish(VECTOR_STORING, {
            "type": "publish",
            "topic": VECTOR_STORING,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "vector_size": len(vector),
                "timestamp": get_timestamp()
            }
        })
        print(f"[Embedding Service] vector.storing published for: {image_id}")

        # Step 5 — publish vector.stored
        broker.publish(VECTOR_STORED, {
            "type": "publish",
            "topic": VECTOR_STORED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "vector_size": len(vector),
                "timestamp": get_timestamp()
            }
        })
        print(f"[Embedding Service] vector.stored published for: {image_id}")
        print(f"[Embedding Service] Pipeline complete for: {image_id} ✓")

    except Exception as e:
        print(f"[Embedding Service] ERROR: {e}")
        broker = Broker()
        broker.publish(EMBEDDING_FAILED, {
            "type": "publish",
            "topic": EMBEDDING_FAILED,
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
    print("[Embedding Service] Starting up...")
    print("[Embedding Service] Listening for embedding.processing events...\n")
    broker.subscribe(EMBEDDING_PROCESSING, handle_embedding_processing)
    broker.listen()

if __name__ == "__main__":
    main()