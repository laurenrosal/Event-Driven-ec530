# Event-Driven Image Annotation and Retrieval System

EC530 Project 2 — Boston University
Lauren Rosales

---

## Overview

A modular, event-driven pipeline for image annotation and retrieval.
The system has two independent flows:

- **Upload flow** — a user submits an image through the CLI, which triggers
  a chain of events through image processing, annotation, and embedding,
  storing results in both a document database and a vector database.

- **Search flow** — a user types a text description through the CLI, which
  sends a query directly to the vector database and returns matching images.

No AI models are trained or implemented. All inference and embedding
components are simulated modules with defined APIs and message contracts.

---

## Project Structure
```
Event-driven/
├── services/
│   ├── cli_service/              # Entry point for upload and search
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   └── test_cli.py
│   ├── upload_service/           # Receives image, fires image.submitted
│   ├── image_processing_service/ # Processes image, fires inference.completed
│   ├── annotation_service/       # Annotates objects, fires annotation.stored
│   ├── embedding_service/        # Creates vector, fires embedding.created
│   └── query_service/            # Handles search queries via vector DB
├── databases/
│   ├── document_db/              # Stores annotation JSON
│   └── vector_db/                # Stores vectors, returns matches (FAISS)
├── messaging/
│   ├── __init__.py
│   ├── topics.py                 # All topic name constants
│   ├── broker.py                 # Redis pub/sub interface
│   └── event_generator.py        # Simulates and replays events for testing
├── tests/
│   └── test_messaging.py         # Unit tests for messaging system
└── README.md
```


---

## Event Flow

### Upload flow AND Search flow 

![My Image](architecture.png)



---

## Topics

| Topic | Publisher | Subscriber |
|---|---|---|
| `image.submitted` | CLI / upload service | Image processing service |
| `inference.completed` | Image processing service | Annotation service |
| `annotation.stored` | Annotation service | Embedding service |
| `embedding.created` | Embedding service | Vector database |
| `annotation.corrected` | CLI / reviewer | Annotation service |
| `query.submitted` | CLI | Query service |
| `query.completed` | Query service | CLI |

---

## Event Schema

All events follow this structure:

```json
{
  "type": "publish",
  "topic": "image.submitted",
  "event_id": "evt_3f2a1b4c",
  "payload": {
    "image_id": "img_9a7c2d1e",
    "path": "images/street_1042.jpg",
    "timestamp": "2026-04-13T14:33:00Z"
  }
}
```

---

## Setup

### Requirements
- Python 3.9+
- Docker

### 1. Clone the repo and navigate to the project
```bash
cd Event-driven
```

### 2. Install dependencies
```bash
pip install redis pytest
```

### 3. Start Redis
```bash
docker run -d -p 6379:6379 --name redis-local redis
```

### 4. Verify Redis is running
```bash
docker ps
```

---

## Running the CLI

### Upload an image
```bash
python3 services/cli_service/cli.py upload images/mycat.jpg
```

### Search for images
```bash
python3 services/cli_service/cli.py search "a cat with a halloween costume"
```

---

## Running the Tests

```bash
python3 -m pytest tests/test_messaging.py -v
```

Expected output: **15 passed**

### What the tests cover
- Valid events contain all required fields (`type`, `topic`, `event_id`, `payload`)
- Malformed events are rejected without crashing the system
- Duplicate events do not create duplicate state
- Event generator works without a live Redis broker (using mocks)
- Deterministic replay mode produces consistent events with a seed

---

## System Guarantees

| Guarantee | Description |
|---|---|
| **Idempotency** | Duplicate events do not create duplicate state |
| **Robustness** | Malformed events are rejected without crashing |
| **Eventual consistency** | System may be temporarily incomplete but converges |
| **Accurate queries** | Queries reflect the current processed state |

---

## What's Not Built Yet (Week 2)

- Annotation service implementation
- Document database service
- Embedding service implementation
- Vector database / FAISS integration
- Query service implementation
- Simulated inference data (provided by instructor next week)
Type that out into a file called README.md in the root of your project folder. Once you've done that you're fully ready for tomorrow — you've got the structure, the messaging system, the tests, and the documentation all done!
