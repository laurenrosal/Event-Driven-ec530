import json
import uuid
import requests
import torch
from datetime import datetime, timezone
from Messaging.broker import Broker
from Messaging.topics import (
    QUERY_SUBMITTED,
    QUERY_COMPLETED,
)
from databases.vector_db.vector_db import VectorDB
from transformers import CLIPProcessor, CLIPModel

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def call_claude(prompt: str) -> str:
    """Call Claude API and return the response text."""
    import os
    from dotenv import load_dotenv
    load_dotenv()

    headers = {
        "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
    data = response.json()
    return data["content"][0]["text"]

def expand_query(description: str) -> str:
    prompt = f"""You are helping search an image database.
A user searched for: "{description}"

Expand this into a short description of visual features in ONE sentence only.
Max 15 words. Only visual details, no extra commentary."""

    try:
        expanded = call_claude(prompt)
        print(f"[Query Service] Claude expanded query: {expanded}")
        return expanded
    except Exception as e:
        print(f"[Query Service] Claude query expansion failed: {e} — using original")
        return description

def rank_results(description: str, results: list) -> str:
    """
    Use Claude to explain the search results to the user.
    """
    if not results:
        return "No matching images found."

    results_text = "\n".join([
        f"{i+1}. {r['path']} (similarity: {r['similarity_score']})"
        for i, r in enumerate(results)
    ])

    prompt = f"""A user searched for: "{description}"

The following images were returned from a vector database search:
{results_text}

In 2-3 sentences, explain these results to the user in a helpful way. 
Mention which result is the best match and why based on the similarity scores.
Keep it conversational and short."""

    try:
        explanation = call_claude(prompt)
        return explanation
    except Exception as e:
        print(f"[Query Service] Claude ranking failed: {e}")
        return f"Found {len(results)} matching images."

# Load CLIP once
print("[Query Service] Loading CLIP model...")
MODEL = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
PROCESSOR = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("[Query Service] CLIP model loaded!")

def text_to_vector(description: str) -> list:
    """Generate a real CLIP text embedding."""
    inputs = PROCESSOR(
        text=[description],
        return_tensors="pt",
        padding=True,
        truncation=True,   
        max_length=77       
    )
    with torch.no_grad():
        embedding = MODEL.get_text_features(**inputs)
    return embedding[0].numpy().tolist()

def handle_query_submitted(message):
    """Handles incoming query.submitted events."""
    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})
        query_id = payload.get("query_id")
        description = payload.get("description")

        print(f"\n[Query Service] Received query: {query_id}")
        print(f"[Query Service] Original description: '{description}'")

        if not description or description.strip() == "":
            raise ValueError("Search description cannot be empty")

        broker = Broker()
        db = VectorDB()

        # Step 1 — use Claude to expand the query
        expanded_description = expand_query(description)

        # Step 2 — convert to vector and search FAISS
        query_vector = text_to_vector(expanded_description)
        results = db.search(query_vector, top_k=3)
        print(f"[Query Service] Found {len(results)} matches")

        # Step 3 — use Claude to explain the results
        explanation = rank_results(description, results)
        print(f"[Query Service] Claude explanation: {explanation}")

        # Step 4 — publish query.completed
        broker.publish(QUERY_COMPLETED, {
            "type": "publish",
            "topic": QUERY_COMPLETED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "query_id": query_id,
                "description": description,
                "expanded_description": expanded_description,
                "results": results,
                "explanation": explanation,
                "total_matches": len(results),
                "timestamp": get_timestamp()
            }
        })
        print(f"[Query Service] query.completed published for: {query_id}")
        print(f"\n[Query Service] Results for '{description}':")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['path']} (score: {result['similarity_score']})")
        print(f"\n[Query Service] {explanation}")

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