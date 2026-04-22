import argparse
import json
import os
import time
import uuid
import hashlib
import random
from datetime import datetime, timezone

from Messaging.broker import Broker
from Messaging.topics import IMAGE_SUBMITTED, QUERY_SUBMITTED
from databases.document_db.document_db import DocumentDB
from databases.vector_db.vector_db import VectorDB
def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def text_to_vector(description: str, dim: int = 128) -> list:
    """
    Deterministic fake text embedding.
    Same query always gives same vector.
    """
    seed_hash = hashlib.md5(description.lower().strip().encode()).hexdigest()
    seed_int = int(seed_hash[:8], 16)

    rng = random.Random(seed_int)
    return [round(rng.uniform(-1, 1), 4) for _ in range(dim)]


def vector_exists_for_image(vector_db: VectorDB, image_id: str) -> bool:
    for _, metadata in vector_db.image_map.items():
        if metadata.get("image_id") == image_id:
            return True
    return False


def upload_image(image_path: str, timeout_seconds: int = 20):
    if not os.path.exists(image_path):
        print(json.dumps({
            "status": "error",
            "message": f"File not found: {image_path}"
        }, indent=2))
        return

    broker = Broker()
    document_db = DocumentDB()
    vector_db = VectorDB()

    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    image_id = f"img_{uuid.uuid4().hex[:8]}"

    event = {
        "type": "publish",
        "topic": IMAGE_SUBMITTED,
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "payload": {
            "batch_id": batch_id,
            "image_id": image_id,
            "path": image_path,
            "timestamp": get_timestamp()
        }
    }

    try:
        broker.publish(IMAGE_SUBMITTED, event)

        mongo_stored = False
        vector_stored = False
        annotation_record = None

        start = time.time()

        while time.time() - start < timeout_seconds:
            try:
                annotation_record = document_db.get_annotation(image_id)
                mongo_stored = annotation_record is not None
            except Exception:
                mongo_stored = False

            try:
                # reload latest FAISS metadata each loop
                vector_db = VectorDB()
                vector_stored = vector_exists_for_image(vector_db, image_id)
            except Exception:
                vector_stored = False

            if mongo_stored and vector_stored:
                break

            time.sleep(1)

        status = "success" if (mongo_stored and vector_stored) else "pending"

        response = {
            "status": status,
            "message": (
                "Complete pipeline finished successfully"
                if status == "success"
                else "Image submitted, but pipeline has not fully finished yet"
            ),
            "image_id": image_id,
            "batch_id": batch_id,
            "path": image_path,
            "mongo_stored": mongo_stored,
            "vector_stored": vector_stored
        }

        if annotation_record:
            annotation = annotation_record.get("annotation", {})
            response["annotation_count"] = annotation.get("annotation_count", 0)
            response["format"] = annotation.get("format")
            response["width"] = annotation.get("width")
            response["height"] = annotation.get("height")

        print(json.dumps(response, indent=2))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2))


def search_images(description: str, top_k: int = 3):
    if not description or description.strip() == "":
        print(json.dumps({
            "status": "error",
            "message": "Search description cannot be empty"
        }, indent=2))
        return

    try:
        broker = Broker()
        event = {
            "type": "publish",
            "topic": QUERY_SUBMITTED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "query_id": f"qry_{uuid.uuid4().hex[:8]}",
                "description": description,
                "top_k": top_k,
                "timestamp": get_timestamp()
            }
        }
        broker.publish(QUERY_SUBMITTED, event)
        print(f"\n[CLI] Search submitted: '{description}'")
        print("[CLI] Results will appear in the query service terminal...")

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2))

def main():
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")

    upload_parser = subparsers.add_parser("upload", help="Upload one image and wait for pipeline completion")
    upload_parser.add_argument("image_path", help="Path to one image")

    search_parser = subparsers.add_parser("search", help="Search for similar images in vector DB")
    search_parser.add_argument("description", help="Search text")
    search_parser.add_argument("--top-k", type=int, default=3, help="Number of matches to return")

    args = parser.parse_args()

    if args.command == "upload":
        upload_image(args.image_path)
    elif args.command == "search":
        search_images(args.description, top_k=args.top_k)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()