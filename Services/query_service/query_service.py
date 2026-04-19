import json
import uuid
import time
import random
from datetime import datetime, timezone
from Messaging.broker import Broker
from Messaging.topics import (
    QUERY_SUBMITTED,
    QUERY_COMPLETED,
)

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def simulate_vector_search(description: str) -> list:
    """
    Simulated vector search.
    Replace this with real FAISS/vector DB logic later.
    """
    time.sleep(1)  # simulate search time
    # return fake matching images
    sample_images = [
        "images/cat.jpg",
        "images/dog.jpg",
        "images/beach.jpg",
        "images/street_1042.jpg",
        "images/city_night.jpg",
    ]
    # return top 3 random matches with fake similarity scores
    matches = random.sample(sample_images, min(3, len(sample_images)))
    return [
        {
            "image_id": f"img_{uuid.uuid4().hex[:8]}",
            "path": match,
            "similarity_score": round(random.uniform(0.75, 0.99), 4)
        }
        for match in matches
    ]

def handle_query_submitted(message):
    """Handles incoming query.submitted events."""
    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})
        query_id = payload.get("query_id")
        description = payload.get("description")

        print(f"\n[Query Service] Received query: {query_id}")
        print(f"[Query Service] Searching for: '{description}'")

        broker = Broker()

        # validate description is not empty
        if not description or description.strip() == "":
            raise ValueError("Search description cannot be empty")

        # Step 1 — simulate vector search
        results = simulate_vector_search(description)
        print(f"[Query Service] Found {len(results)} matches")

        # Step 2 — publish query.completed with results
        broker.publish(QUERY_COMPLETED, {
            "type": "publish",
            "topic": QUERY_COMPLETED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "query_id": query_id,
                "description": description,
                "results": results,
                "total_matches": len(results),
                "timestamp": get_timestamp()
            }
        })
        print(f"[Query Service] query.completed published for: {query_id}")
        print(f"\n[Query Service] Results for '{description}':")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['path']} (score: {result['similarity_score']})")

    except Exception as e:
        print(f"[Query Service] ERROR: {e}")

def main():
    broker = Broker()
    print("[Query Service] Starting up...")
    print("[Query Service] Listening for query.submitted events...\n")
    broker.subscribe(QUERY_SUBMITTED, handle_query_submitted)
    broker.listen()

if __name__ == "__main__":
    main()