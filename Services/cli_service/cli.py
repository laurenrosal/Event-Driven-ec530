import argparse
import json
import uuid
from datetime import datetime, timezone
from Messaging.broker import Broker
from Messaging.topics import IMAGE_SUBMITTED, QUERY_SUBMITTED

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def upload_batch(image_paths: list):
    broker = Broker()
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    print(f"\n[CLI] Starting batch upload: {batch_id}")
    print(f"[CLI] Total images: {len(image_paths)}\n")

    for image_path in image_paths:
        event = {
            "type": "publish",
            "topic": IMAGE_SUBMITTED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "batch_id": batch_id,
                "image_id": f"img_{uuid.uuid4().hex[:8]}",
                "path": image_path,
                "timestamp": get_timestamp()
            }
        }
        try:
            broker.publish(IMAGE_SUBMITTED, event)
            print(f"[CLI] Submitted: {image_path}")
        except ValueError as e:
            print(f"[CLI] Rejected: {image_path} — {e}")

    print(f"\n[CLI] Batch {batch_id} submitted successfully!")

def search(description: str):
    broker = Broker()
    event = {
        "type": "publish",
        "topic": QUERY_SUBMITTED,
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "payload": {
            "query_id": f"qry_{uuid.uuid4().hex[:8]}",
            "description": description,
            "timestamp": get_timestamp()
        }
    }
    try:
        broker.publish(QUERY_SUBMITTED, event)
        print(f"\n[CLI] Search submitted: '{description}'")
    except ValueError as e:
        print(f"[CLI] Search rejected — {e}")

def main():
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")

    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument(
        "image_paths",
        nargs="+",  # accepts one or more images
        help="One or more image paths to upload"
    )

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("description")

    args = parser.parse_args()

    if args.command == "upload":
        upload_batch(args.image_paths)
    elif args.command == "search":
        search(args.description)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()