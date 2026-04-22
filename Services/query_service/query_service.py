import hashlib
import random
from databases.vector_db.vector_db import VectorDB

class QueryService:
    def __init__(self):
        self.db = VectorDB()

    def text_to_vector(self, description: str, dim: int = 128) -> list:
        """
        Deterministic fake query embedding.
        Same query always gives same vector.
        """
        seed_hash = hashlib.md5(description.lower().strip().encode()).hexdigest()
        seed_int = int(seed_hash[:8], 16)

        rng = random.Random(seed_int)
        return [round(rng.uniform(-1, 1), 4) for _ in range(dim)]

    def search_images(self, description: str, top_k: int = 3):
        if not description or description.strip() == "":
            raise ValueError("Search description cannot be empty")

        query_vector = self.text_to_vector(description)
        results = self.db.search(query_vector, top_k=top_k)

        return [
            {
                "image_id": item.get("image_id"),
                "file_name": item.get("file_name"),
                "path": item.get("path"),
                "similarity_score": item.get("similarity_score")
            }
            for item in results
        ]