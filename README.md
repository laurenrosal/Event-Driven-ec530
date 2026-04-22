# Event-Driven Image Annotation and Retrieval System

EC530 Project 2 — Boston University
Lauren Rosales

---

## Overview

A modular event-driven pipeline for image annotation and retrieval. The system has two flows:

- **Upload flow** — upload images through the CLI, each image is tracked individually through YOLO object detection, annotation storage in MongoDB, CLIP embedding generation, and vector storage in FAISS.
- **Search flow** — type a description through the CLI, Claude expands the query, FAISS finds the closest matching images, and Claude explains the results.

![Architecture](architecture.png)
![Flow](flow.png)

---

## Stack

- **Messaging** — Redis Cloud (pub/sub)
- **Object Detection** — YOLOv8 (COCO pre-trained)
- **Document DB** — MongoDB Atlas (annotation JSON)
- **Embeddings** — CLIP (openai/clip-vit-base-patch32, 512-dim)
- **Vector DB** — FAISS (cosine similarity)
- **Query Intelligence** — Claude API (query expansion + result explanation)

---

## Project Structure

```
Event-driven/
├── Services/
│   ├── cli_service/              # Entry point for upload, search, correction
│   ├── upload_service/           # Validates and tracks each image
│   ├── image_processing_service/ # YOLO object detection
│   ├── annotation_service/       # Stores annotations, handles corrections
│   ├── embedding_service/        # CLIP embedding generation
│   └── query_service/            # Claude + FAISS search
├── databases/
│   ├── document_db/              # MongoDB interface
│   └── vector_db/                # FAISS interface
├── Messaging/
│   ├── broker.py                 # Redis pub/sub interface
│   └── topics.py                 # All topic name constants
├── tests/
├── .env
└── README.md
```

---

## Setup

```bash
pip install redis pymongo faiss-cpu numpy python-dotenv torch torchvision transformers Pillow ultralytics requests
```

Create a `.env` file in the root:
```
REDIS_HOST=your-host
REDIS_PORT=your-port
REDIS_PASSWORD=your-password
MONGO_URI=your-mongo-uri
MONGO_DB_NAME=event_driven_db
ANTHROPIC_API_KEY=your-api-key
```

---

## Running the pipeline

Open 5 terminals:

```bash
# Terminal 1
python3 -m Services.upload_service.upload_service

# Terminal 2
python3 -m Services.image_processing_service.image_processing_service

# Terminal 3
python3 -m Services.annotation_service.annotation_service

# Terminal 4
python3 -m Services.embedding_service.embedding_service

# Terminal 5 — upload an image
python3 -m Services.cli_service.cli upload images/cat.jpg

# Terminal 5 — search
python3 -m Services.cli_service.cli search "a cat with a halloween costume"

# Terminal 5 — correct an annotation
python3 -m Services.cli_service.cli correct img_xxxx "cat" "kitten"
```

---

## Topics

| Topic | Publisher | Subscriber |
|---|---|---|
| `image.submitted` | CLI | Upload service |
| `image.received` | Upload service | — |
| `image.validated` | Upload service | — |
| `image.invalid` | Upload service | — |
| `image.processing` | Upload service | Image processing service |
| `image.processing.complete` | Image processing service | — |
| `annotation.storing` | Image processing service | Annotation service |
| `image.annotating` | Annotation service | — |
| `annotation.stored` | Annotation service | — |
| `image.annotated` | Annotation service | — |
| `annotation.corrected` | CLI | Annotation service |
| `embedding.processing` | Annotation service | Embedding service |
| `embedding.complete` | Embedding service | — |
| `vector.storing` | Embedding service | — |
| `vector.stored` | Embedding service | — |
| `image.failed` | Any service on error | — |
| `annotation.failed` | Annotation service on error | — |
| `embedding.failed` | Embedding service on error | — |
| `query.submitted` | CLI | Query service |
| `query.completed` | Query service | — |

---

## Tests

```bash
python3 -m pytest tests/ -v
```

28 tests covering event structure, malformed event rejection, valid file types, idempotency, mock broker, and topic definitions.

---

## CLI Commands

| Command | Description |
|---|---|
| `cli upload images/cat.jpg` | Upload a single image |
| `cli search "a dog in a park"` | Search for matching images |
| `cli correct img_xxxx "cat" "kitten"` | Correct an annotation |