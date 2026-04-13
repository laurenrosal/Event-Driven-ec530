import argparse
import json
import uuid
from datetime import datetime, timezone
from Messaging.broker import Broker

def upload(image_path: str):
    # connect the broker and pushlish image.submitted event
    event ={
        "type": "publish",
        "topic": "image.submitted",
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "payload": {
            "image_id": f"img_{uuid.uuid4().hex[:8]}",
            "path": image_path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    #publishes an image.submitted event to the message broker.
    print(f"[CLI] Uploading image: {image_path}")
    print(json.dumps(event, indent=2))
    broker = Broker()
    broker.publish(event["topic"], event)

def search(description: str):

    # connect to broker and publish query.submitted event
    event = {
        "type": "publish",
        "topic": "query.submitted",
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "payload": {
            "query_id": f"qry_{uuid.uuid4().hex[:8]}",
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    # pulished a query.submitted event to the message broker
    print(f"[CLI] searching for: {description}")
    print(json.dumps(event, indent=2))
    broker = Broker()
    broker.publish(event["topic"], event)

def main():
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")


    upload_parser = subparsers.add_parser(upload)
    upload_parser.add_argument("image_path")


    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("description")

    args = parser.parse_args()

    if args.command == "upload":
        upload(args.image_path)
    elif args.command == search:
        search(args.description)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
