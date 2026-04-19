import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

class DocumentDB:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client[os.getenv("MONGO_DB_NAME", "event_driven_db")]
        self.collection = self.db["annotations"]

    def test_connection(self):
        try:
            self.client.admin.command("ping")
            print("[Document DB] Connected to MongoDB Atlas!")
            return True
        except Exception as e:
            print(f"[Document DB] Connection failed: {e}")
            return False

    def store_annotation(self, image_id: str, batch_id: str, path: str, annotation: dict):
        """Store annotation JSON for an image."""
        try:
            # check if already exists (idempotency)
            existing = self.collection.find_one({"image_id": image_id})
            if existing:
                print(f"[Document DB] Annotation already exists for: {image_id} — skipping")
                return existing["_id"]

            record = {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "annotation": annotation,
                "status": "stored",
                "created_at": get_timestamp()
            }

            result = self.collection.insert_one(record)
            print(f"[Document DB] Stored annotation for: {image_id} — _id: {result.inserted_id}")
            return result.inserted_id

        except Exception as e:
            print(f"[Document DB] ERROR storing annotation: {e}")
            raise

    def get_annotation(self, image_id: str):
        """Retrieve annotation for a specific image."""
        try:
            record = self.collection.find_one({"image_id": image_id})
            if record:
                record["_id"] = str(record["_id"])
                print(f"[Document DB] Retrieved annotation for: {image_id}")
                return record
            else:
                print(f"[Document DB] No annotation found for: {image_id}")
                return None
        except Exception as e:
            print(f"[Document DB] ERROR retrieving annotation: {e}")
            raise

    def get_batch(self, batch_id: str):
        """Retrieve all annotations for a batch."""
        try:
            records = list(self.collection.find({"batch_id": batch_id}))
            for record in records:
                record["_id"] = str(record["_id"])
            print(f"[Document DB] Retrieved {len(records)} records for batch: {batch_id}")
            return records
        except Exception as e:
            print(f"[Document DB] ERROR retrieving batch: {e}")
            raise