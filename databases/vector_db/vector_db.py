import os
import json
import numpy as np
import faiss
from datetime import datetime, timezone

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

class VectorDB:
    def __init__(self, dimension=128):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance search
        self.image_map = {}  # maps index position → image metadata
        self.next_id = 0
        self.index_file = "databases/vector_db/faiss.index"
        self.map_file = "databases/vector_db/image_map.json"
        self._load()

    def test_connection(self):
        try:
            total = self.index.ntotal
            print(f"[Vector DB] FAISS index ready! Vectors stored: {total}")
            return True
        except Exception as e:
            print(f"[Vector DB] ERROR: {e}")
            return False

    def store_vector(self, image_id: str, batch_id: str, path: str, vector: list):
        """Store a vector in the FAISS index."""
        try:
            # check idempotency
            for key, val in self.image_map.items():
                if val["image_id"] == image_id:
                    print(f"[Vector DB] Vector already exists for: {image_id} — skipping")
                    return

            # convert to numpy array
            np_vector = np.array([vector], dtype=np.float32)

            # add to FAISS index
            self.index.add(np_vector)

            # store metadata
            self.image_map[str(self.next_id)] = {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "stored_at": get_timestamp()
            }
            self.next_id += 1

            # save to disk
            self._save()

            print(f"[Vector DB] Stored vector for: {image_id} — total vectors: {self.index.ntotal}")

        except Exception as e:
            print(f"[Vector DB] ERROR storing vector: {e}")
            raise

    def search(self, query_vector: list, top_k: int = 3):
        """Search for top k similar vectors."""
        try:
            if self.index.ntotal == 0:
                print("[Vector DB] No vectors stored yet!")
                return []

            np_vector = np.array([query_vector], dtype=np.float32)
            distances, indices = self.index.search(np_vector, min(top_k, self.index.ntotal))

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:
                    continue
                metadata = self.image_map.get(str(idx), {})
                results.append({
                    "image_id": metadata.get("image_id"),
                    "path": metadata.get("path"),
                    "similarity_score": round(float(1 / (1 + dist)), 4)
                })

            print(f"[Vector DB] Found {len(results)} matches")
            return results

        except Exception as e:
            print(f"[Vector DB] ERROR searching: {e}")
            raise

    def _save(self):
        """Save FAISS index and image map to disk."""
        faiss.write_index(self.index, self.index_file)
        with open(self.map_file, "w") as f:
            json.dump(self.image_map, f, indent=2)

    def _load(self):
        """Load FAISS index and image map from disk if they exist."""
        if os.path.exists(self.index_file) and os.path.exists(self.map_file):
            self.index = faiss.read_index(self.index_file)
            with open(self.map_file, "r") as f:
                self.image_map = json.load(f)
            self.next_id = len(self.image_map)
            print(f"[Vector DB] Loaded existing index — vectors: {self.index.ntotal}")
        else:
            print("[Vector DB] Starting fresh index")