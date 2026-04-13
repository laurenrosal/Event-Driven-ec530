import redis
import json
from Messaging.topics import ALL_TOPICS

class Broker:
    def __inti__(self, host="localhost", port=6379):
        self.client = redis.Redis(host=host, port=port, decode_reponses=True)
        self.pubsub = self.client.pubsub()
    

    def publish(self, topic: str, event: dict):
        if topic not in ALL_TOPICS: 
            raise ValueError(f"unknown topic: {topic}")
        if not self._is_valid_event(event):
            raise ValueError(f"Malformed event: {event}")
        message = json.dumps(event)
        self.client.publish(topic, message)
        print(f"[Broker] Published to {topic}: {event['event_id']}" )


    def subscribe(self, topic:str, handler):
        if topic not in ALL_TOPICS:
            raise ValueError(f"unknown topic: {topic}")
        self.pubsub.subscribe(**{topic: handler})
        print(f"[Broker] Subscribed to {topic}")

    
    def listen(self):
        print("[Broker] Listening for messages....")
        for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                print(f"[Broker] Received on {message['channel']}: {data}")
    

    def _is_valid_event(self, event: dict) -> bool:
        required_fields = {"type", "topic", "event_id", "payload"}
        return required_fields.issubset(event.keys())