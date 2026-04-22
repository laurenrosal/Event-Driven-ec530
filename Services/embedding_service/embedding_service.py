import json
import uuid
import time
import random
import hashlib
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

def simulate_embedding(image_id: str, annotation: dict, path: str = "") -> list:
    """
    Generates a deterministic fake embedding vector.
    Same image/path/annotation -> same vector every time.
    Good for testing vector DB workflows.
    """
    time.sleep(1)  # simulate embedding time

    # Build a stable seed from image data
    seed_input = f"{image_id}|{path}|{json.dumps(annotation, sort_keys=True)}"
    seed_hash = hashlib.md5(seed_input.encode()).hexdigest()
    seed_int = int(seed_hash[:8], 16)

    rng = random.Random(seed_int)

    # Return a fake vector of 128 dimensions
    return [round(rng.uniform(-1, 1), 4) for _ in range(128)]

def handle_embedding_processing(message):
    """Handles incoming embedding.processing events."""
    image_id = None
    batch_id = None

    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})

        image_id = payload.get("image_id")
        batch_id = payload.get("batch_id")
        annotation = payload.get("annotation", {})
        path = payload.get("path", "")

        print(f"\n[Embedding Service] Received image: {image_id}")

        broker = Broker()

        # Step 1 — generate deterministic fake embedding
        vector = simulate_embedding(image_id, annotation, path)
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

        # Step 3 — store vector in vector DB
        db = VectorDB()
        db.store_vector(
            image_id=image_id,
            batch_id=batch_id,
            path=path,
            vector=vector
        )
        print(f"[Embedding Service] Vector stored in DB for: {image_id}")

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