import uuid
import json
import random
from datetime import datetime, timezone
from Messaging.topics import IMAGE_SUBMITTED, QUERY_SUBMITTED

SAMPLE_IMAGES = [
    "images/cat_halloween.jpg",
    "images/dog_park.jpg",
    "images/street_1042.jpg",
    "images/beach_sunset.jpg",
    "images/city_night.jpg",
]

SAMPLE_QUERIES = [
    "a cat with a halloween costume",
    "a dog in the park",
    "people walking on a street",
    "sunset at the beach",
    "city lights at night",
]

class EventGenerator:
    def __init__(self, broker=None, seed=None):
        self.broker = broker
        if seed is not None:
            random.seed(seed)  # deterministic mode

    def make_image_event(self, image_path=None):
        return {
            "type": "publish",
            "topic": IMAGE_SUBMITTED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": f"img_{uuid.uuid4().hex[:8]}",
                "path": image_path or random.choice(SAMPLE_IMAGES),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    def make_query_event(self, description=None):
        return {
            "type": "publish",
            "topic": QUERY_SUBMITTED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "query_id": f"qry_{uuid.uuid4().hex[:8]}",
                "description": description or random.choice(SAMPLE_QUERIES),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    def emit(self, event: dict):
        if self.broker:
            self.broker.publish(event["topic"], event)
        else:
            print(f"[EventGenerator] No broker attached, printing event:")
            print(json.dumps(event, indent=2))

    def replay(self, events: list):
        print(f"[EventGenerator] Replaying {len(events)} events...")
        for event in events:
            self.emit(event)

    def generate_batch(self, count=5):
        events = []
        for _ in range(count):
            if random.random() > 0.5:
                events.append(self.make_image_event())
            else:
                events.append(self.make_query_event())
        return events