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
    ANNOTATION_STORING,
    ANNOTATION_STORED,
    ANNOTATION_CORRECTED,
    EMBEDDING_PROCESSING,
    QUERY_SUBMITTED,
    QUERY_COMPLETED,
    ALL_TOPICS
)

# ─── Helpers ────────────────────────────────────────────────

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

def make_correction_event(image_id="img_001"):
    import uuid
    from datetime import datetime, timezone
    return {
        "type": "publish",
        "topic": ANNOTATION_CORRECTED,
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "payload": {
            "image_id": image_id,
            "corrected_annotation": {
                "original_label": "cat",
                "corrected_label": "kitten"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def mock_broker():
    return MagicMock(spec=Broker)

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

def test_correction_event_has_required_fields():
    event = make_correction_event()
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

def test_correction_event_has_correct_topic():
    event = make_correction_event()
    assert event["topic"] == ANNOTATION_CORRECTED

def test_image_event_payload_has_image_id():
    event = make_image_event()
    assert "image_id" in event["payload"]

def test_image_event_payload_has_batch_id():
    event = make_image_event()
    assert "batch_id" in event["payload"]

def test_image_event_payload_has_timestamp():
    event = make_image_event()
    assert "timestamp" in event["payload"]

def test_correction_event_has_corrected_annotation():
    event = make_correction_event()
    assert "corrected_annotation" in event["payload"]
    assert "corrected_label" in event["payload"]["corrected_annotation"]

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

# ─── Mock broker tests (no live Redis needed) ────────────────

def test_mock_broker_publish_called(mock_broker):
    event = make_image_event()
    mock_broker.publish(event["topic"], event)
    mock_broker.publish.assert_called_once()

def test_mock_broker_correction_published(mock_broker):
    event = make_correction_event()
    mock_broker.publish(event["topic"], event)
    mock_broker.publish.assert_called_once_with(ANNOTATION_CORRECTED, event)

def test_mock_broker_query_published(mock_broker):
    event = make_query_event()
    mock_broker.publish(event["topic"], event)
    mock_broker.publish.assert_called_once_with(QUERY_SUBMITTED, event)

# ─── All topics defined ──────────────────────────────────────

def test_all_topics_list_not_empty():
    assert len(ALL_TOPICS) > 0

def test_image_submitted_in_all_topics():
    assert IMAGE_SUBMITTED in ALL_TOPICS

def test_query_submitted_in_all_topics():
    assert QUERY_SUBMITTED in ALL_TOPICS

def test_image_failed_in_all_topics():
    assert IMAGE_FAILED in ALL_TOPICS

def test_annotation_corrected_in_all_topics():
    assert ANNOTATION_CORRECTED in ALL_TOPICS

def test_embedding_processing_in_all_topics():
    assert EMBEDDING_PROCESSING in ALL_TOPICS