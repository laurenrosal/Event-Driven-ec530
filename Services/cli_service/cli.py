import argparse
import json
import os
import uuid
from datetime import datetime, timezone

from Messaging.broker import Broker
from Messaging.topics import IMAGE_SUBMITTED, QUERY_SUBMITTED, ANNOTATION_CORRECTED

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def upload_image(image_path: str):
    if not os.path.exists(image_path):
        print(json.dumps({
            "status": "error",
            "message": f"File not found: {image_path}"
        }, indent=2))
        return

    broker = Broker()
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
        print(json.dumps({
            "status": "submitted",
            "message": "Image submitted to pipeline successfully",
            "image_id": image_id,
            "batch_id": batch_id,
            "path": image_path,
            "timestamp": get_timestamp()
        }, indent=2))

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

def correct_annotation(image_id: str, label: str, new_label: str):
    """Submit a correction for an annotation."""
    try:
        broker = Broker()
        event = {
            "type": "publish",
            "topic": ANNOTATION_CORRECTED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "corrected_annotation": {
                    "original_label": label,
                    "corrected_label": new_label,
                    "corrected_at": get_timestamp()
                },
                "timestamp": get_timestamp()
            }
        }
        broker.publish(ANNOTATION_CORRECTED, event)
        print(json.dumps({
            "status": "submitted",
            "message": f"Correction submitted for {image_id}",
            "original_label": label,
            "corrected_label": new_label
        }, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=2))

def main():
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")

    upload_parser = subparsers.add_parser("upload", help="Upload one image and wait for pipeline completion")
    upload_parser.add_argument("image_path", help="Path to one image")

    search_parser = subparsers.add_parser("search", help="Search for similar images in vector DB")
    search_parser.add_argument("description", help="Search text")
    search_parser.add_argument("--top-k", type=int, default=3, help="Number of matches to return")

    correct_parser = subparsers.add_parser("correct", help="Correct an annotation")
    correct_parser.add_argument("image_id", help="Image ID to correct")
    correct_parser.add_argument("label", help="Original label")
    correct_parser.add_argument("new_label", help="Corrected label")

    args = parser.parse_args()

    if args.command == "upload":
        upload_image(args.image_path)
    elif args.command == "search":
        search_images(args.description, top_k=args.top_k)
    elif args.command == "correct":
        correct_annotation(args.image_id, args.label, args.new_label)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()