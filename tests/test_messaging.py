import pytest
from unittest.mock import MagicMock, patch
from Messaging.broker import Broker
from Messaging.topics import (
    IMAGE_SUBMITTED,
    IMAGE_RECEIVED,
    IMAGE_VALIDATED,
    IMAGE_INVALID,
    IMAGE_PROCESSING,
    IMAGE_FAILED,
    QUERY_SUBMITTED,
    QUERY_COMPLETED,
    ALL_TOPICS
)
# python3 -m pytest tests/test_messaging.py -v 

# ─── Fixtures ───────────────────────────────────────────────

@pytest.fixture
def mock_broker():
    broker = MagicMock(spec=Broker)
    return broker

def make_image_event(path="images/cat.jpg"):
    import uuid
    from datetime import datetime, timezone
    return {
        "type": "publish",
        "topic": IMAGE_SUBMITTED,
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "payload": {
            "batch_id": f"batch_{uuid.uuid4().hex[:8]}",
            "image_id": f"img_{uuid.uuid4().hex[:8]}",
            "path": path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

def make_query_event(description="a cat with a halloween costume"):
    import uuid
    from datetime import datetime, timezone
    return {
        "type": "publish",
        "topic": QUERY_SUBMITTED,
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "payload": {
            "query_id": f"qry_{uuid.uuid4().hex[:8]}",
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

# ─── Valid event structure ───────────────────────────────────

def test_image_event_has_required_fields():
    event = make_image_event()
    assert "type" in event
    assert "topic" in event
    assert "event_id" in event
    assert "payload" in event

def test_query_event_has_required_fields():
    event = make_query_event()
    assert "type" in event
    assert "topic" in event
    assert "event_id" in event
    assert "payload" in event

def test_image_event_has_correct_topic():
    event = make_image_event()
    assert event["topic"] == IMAGE_SUBMITTED

def test_query_event_has_correct_topic():
    event = make_query_event()
    assert event["topic"] == QUERY_SUBMITTED

def test_image_event_payload_has_image_id():
    event = make_image_event()
    assert "image_id" in event["payload"]

def test_image_event_payload_has_batch_id():
    event = make_image_event()
    assert "batch_id" in event["payload"]

def test_image_event_payload_has_timestamp():
    event = make_image_event()
    assert "timestamp" in event["payload"]

# ─── Malformed events ────────────────────────────────────────

def test_broker_rejects_missing_event_id():
    broker = Broker()
    bad_event = {
        "type": "publish",
        "topic": IMAGE_SUBMITTED,
        "payload": {"image_id": "img_001"}
    }
    with pytest.raises(ValueError):
        broker.publish(bad_event["topic"], bad_event)

def test_broker_rejects_unknown_topic():
    broker = Broker()
    bad_event = {
        "type": "publish",
        "topic": "unknown.topic",
        "event_id": "evt_001",
        "payload": {}
    }
    with pytest.raises(ValueError):
        broker.publish(bad_event["topic"], bad_event)

def test_broker_rejects_empty_event():
    broker = Broker()
    with pytest.raises(ValueError):
        broker.publish(IMAGE_SUBMITTED, {})

def test_broker_rejects_invalid_file_type():
    broker = Broker()
    bad_event = make_image_event(path="documents/report.pdf")
    with pytest.raises(ValueError):
        broker.publish(IMAGE_SUBMITTED, bad_event)

# ─── Valid file types ────────────────────────────────────────

def test_broker_accepts_jpg():
    broker = Broker()
    event = make_image_event(path="images/cat.jpg")
    broker.publish(IMAGE_SUBMITTED, event)

def test_broker_accepts_png():
    broker = Broker()
    event = make_image_event(path="images/cat.png")
    broker.publish(IMAGE_SUBMITTED, event)

def test_broker_accepts_jpeg():
    broker = Broker()
    event = make_image_event(path="images/cat.jpeg")
    broker.publish(IMAGE_SUBMITTED, event)

# ─── Idempotency ─────────────────────────────────────────────

def test_duplicate_event_ids_are_equal():
    event1 = make_image_event()
    event2 = event1.copy()
    assert event1["event_id"] == event2["event_id"]

def test_duplicate_events_call_publish_twice(mock_broker):
    event = make_image_event()
    mock_broker.publish(event["topic"], event)
    mock_broker.publish(event["topic"], event)
    assert mock_broker.publish.call_count == 2

# ─── All topics defined ──────────────────────────────────────

def test_all_topics_list_not_empty():
    assert len(ALL_TOPICS) > 0

def test_image_submitted_in_all_topics():
    assert IMAGE_SUBMITTED in ALL_TOPICS

def test_query_submitted_in_all_topics():
    assert QUERY_SUBMITTED in ALL_TOPICS

def test_image_failed_in_all_topics():
    assert IMAGE_FAILED in ALL_TOPICS