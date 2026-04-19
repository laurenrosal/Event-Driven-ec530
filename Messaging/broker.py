import redis
import json
import os
from dotenv import load_dotenv
from Messaging.topics import ALL_TOPICS

load_dotenv()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

class Broker:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
        self.pubsub = self.client.pubsub()

    def test_connection(self):
        try:
            self.client.ping()
            print("[Broker] Connected to Redis Cloud!")
            return True
        except Exception as e:
            print(f"[Broker] Connection failed: {e}")
            return False

    def publish(self, topic: str, event: dict):
        if topic not in ALL_TOPICS:
            raise ValueError(f"Unknown topic: {topic}")
        if not self._is_valid_event(event):
            raise ValueError(f"Malformed event: {event}")
        if topic == "image.submitted":
            path = event.get("payload", {}).get("path", "")
            if not self._is_valid_image(path):
                raise ValueError(f"Invalid file type: {path}")
        message = json.dumps(event)
        self.client.publish(topic, message)
        print(f"[Broker] Published to {topic}: {event['event_id']}")

    def subscribe(self, topic: str, handler):
        if topic not in ALL_TOPICS:
            raise ValueError(f"Unknown topic: {topic}")
        self.pubsub.subscribe(**{topic: handler})
        print(f"[Broker] Subscribed to {topic}")

    def listen(self):
        print("[Broker] Listening for messages...")
        for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                print(f"[Broker] Received on {message['channel']}: {data}")

    def _is_valid_event(self, event: dict) -> bool:
        required_fields = {"type", "topic", "event_id", "payload"}
        return required_fields.issubset(event.keys())

    def _is_valid_image(self, path: str) -> bool:
        import os as _os
        _, ext = _os.path.splitext(path)
        return ext.lower() in ALLOWED_EXTENSIONS