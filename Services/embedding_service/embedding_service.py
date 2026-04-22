import json
import uuid
from datetime import datetime, timezone
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
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

# Load CLIP once
print("[Embedding Service] Loading CLIP model...")
MODEL = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
PROCESSOR = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("[Embedding Service] CLIP model loaded!")

def generate_clip_embedding(image_path: str) -> list:
    """Generate a real CLIP image embedding."""
    image = Image.open(image_path).convert("RGB")
    inputs = PROCESSOR(images=image, return_tensors="pt")
    with torch.no_grad():
        embedding = MODEL.get_image_features(**inputs)
    vector = embedding[0].numpy().tolist()
    return vector

def handle_embedding_processing(message):
    image_id = None
    batch_id = None
    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})
        image_id = payload.get("image_id")
        batch_id = payload.get("batch_id")
        path = payload.get("path")
        annotation = payload.get("annotation", {})

        print(f"\n[Embedding Service] Received image: {image_id}")
        print(f"[Embedding Service] Generating CLIP embedding for: {path}")

        broker = Broker()

        # Step 1 — generate real CLIP embedding
        vector = generate_clip_embedding(path)
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

        # Step 3 — store in vector DB
        db = VectorDB()
        db.store_vector(
            image_id=image_id,
            batch_id=batch_id,
            path=path,
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