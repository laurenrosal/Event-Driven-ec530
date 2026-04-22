import json
import uuid
import os
from datetime import datetime, timezone

from ultralytics import YOLO
from dotenv import load_dotenv

from Messaging.broker import Broker
from Messaging.topics import (
    IMAGE_PROCESSING,
    IMAGE_PROCESSING_COMPLETE,
    ANNOTATION_STORING,
    IMAGE_FAILED
)

load_dotenv()

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

# Load YOLO once
MODEL = YOLO("yolov8n.pt")

def run_coco_detection(image_path: str) -> dict:
    """
    Runs COCO object detection on an image using YOLO.
    Returns image metadata + annotation boxes.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    results = MODEL(image_path)

    annotations = []
    width = None
    height = None
    image_format = os.path.splitext(image_path)[1].replace(".", "").upper()

    for result in results:
        if result.orig_shape:
            height, width = result.orig_shape

        boxes = result.boxes
        if boxes is None:
            continue

        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0].item())
            cls_id = int(box.cls[0].item())
            class_name = MODEL.names[cls_id]

            annotations.append({
                "annotation_id": f"ann_{uuid.uuid4().hex[:8]}",
                "class_id": cls_id,
                "class_name": class_name,
                "confidence": round(conf, 4),
                "bbox": {
                    "x1": round(xyxy[0], 2),
                    "y1": round(xyxy[1], 2),
                    "x2": round(xyxy[2], 2),
                    "y2": round(xyxy[3], 2)
                }
            })

    return {
        "width": width,
        "height": height,
        "format": image_format,
        "processed": True,
        "annotation_count": len(annotations),
        "annotations": annotations
    }

def handle_image_processing(message):
    image_id = None
    batch_id = None

    try:
        data = json.loads(message["data"])
        payload = data.get("payload", {})

        image_id = payload.get("image_id")
        batch_id = payload.get("batch_id")
        path = payload.get("path")

        print(f"\n[Image Processing] Processing image: {image_id}")
        print(f"[Image Processing] Path: {path}")

        broker = Broker()

        # Step 1 — run YOLO detection
        result = run_coco_detection(path)
        print(f"[Image Processing] Done processing: {image_id}")
        print(f"[Image Processing] Found {result['annotation_count']} annotations")

        # Step 2 — publish processing complete
        broker.publish(IMAGE_PROCESSING_COMPLETE, {
            "type": "publish",
            "topic": IMAGE_PROCESSING_COMPLETE,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "result": result,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Image Processing] image.processing.complete published for: {image_id}")

        # Step 3 — hand off real annotation JSON to annotation service
        broker.publish(ANNOTATION_STORING, {
            "type": "publish",
            "topic": ANNOTATION_STORING,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "path": path,
                "annotation": result,
                "timestamp": get_timestamp()
            }
        })
        print(f"[Image Processing] annotation.storing published for: {image_id}")

    except Exception as e:
        print(f"[Image Processing] ERROR: {e}")
        broker = Broker()
        broker.publish(IMAGE_FAILED, {
            "type": "publish",
            "topic": IMAGE_FAILED,
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "payload": {
                "image_id": image_id,
                "batch_id": batch_id,
                "reason": str(e),
                "timestamp": get_timestamp()
            }
        })

def main():
    broker = Broker()
    print("[Image Processing] Starting up...")
    print("[Image Processing] Listening for image.processing events...\n")
    broker.subscribe(IMAGE_PROCESSING, handle_image_processing)
    broker.listen()

if __name__ == "__main__":
    main()