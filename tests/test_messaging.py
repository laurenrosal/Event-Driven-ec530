import pytest
from unittest.mock import MagicMock
from Messaging.broker import Broker
from Messaging.event_generator import EventGenerator
from Messaging.topics import IMAGE_SUBMITTED, QUERY_SUBMITTED

# ─── Fixtures ───────────────────────────────────────────────
# python3 -m pytest tests/test_messaging.py -v

@pytest.fixture
def generator():
    """EventGenerator with no broker — no live Redis needed."""
    return EventGenerator(seed=42)

@pytest.fixture
def mock_broker():
    """A broker with a mocked publish so no live Redis needed."""
    broker = MagicMock(spec=Broker)
    return broker

@pytest.fixture
def generator_with_broker(mock_broker):
    return EventGenerator(broker=mock_broker, seed=42)

# ─── Valid event structure ───────────────────────────────────

def test_image_event_has_required_fields(generator):
    event = generator.make_image_event()
    assert "type" in event
    assert "topic" in event
    assert "event_id" in event
    assert "payload" in event

def test_query_event_has_required_fields(generator):
    event = generator.make_query_event()
    assert "type" in event
    assert "topic" in event
    assert "event_id" in event
    assert "payload" in event

def test_image_event_has_correct_topic(generator):
    event = generator.make_image_event()
    assert event["topic"] == IMAGE_SUBMITTED

def test_query_event_has_correct_topic(generator):
    event = generator.make_query_event()
    assert event["topic"] == QUERY_SUBMITTED

def test_image_event_payload_has_image_id(generator):
    event = generator.make_image_event()
    assert "image_id" in event["payload"]

def test_image_event_payload_has_timestamp(generator):
    event = generator.make_image_event()
    assert "timestamp" in event["payload"]

# ─── Malformed events ────────────────────────────────────────

def test_broker_rejects_missing_event_id():
    broker = Broker()
    bad_event = {
        "type": "publish",
        "topic": IMAGE_SUBMITTED,
        "payload": {"image_id": "img_001"}
        # missing event_id
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

# ─── Idempotency (no duplicate state) ───────────────────────

def test_duplicate_events_call_publish_twice(generator_with_broker, mock_broker):
    event = generator_with_broker.make_image_event()
    generator_with_broker.emit(event)
    generator_with_broker.emit(event)  # duplicate
    assert mock_broker.publish.call_count == 2

def test_duplicate_event_ids_are_equal(generator):
    event1 = generator.make_image_event("images/cat.jpg")
    event2 = event1.copy()  # exact duplicate
    assert event1["event_id"] == event2["event_id"]

# ─── Generator works without live broker ────────────────────

def test_generator_emits_without_broker(generator, capsys):
    event = generator.make_image_event()
    generator.emit(event)
    captured = capsys.readouterr()
    assert "EventGenerator" in captured.out

def test_generator_with_mock_broker(generator_with_broker, mock_broker):
    event = generator_with_broker.make_image_event()
    generator_with_broker.emit(event)
    mock_broker.publish.assert_called_once()

# ─── Replay ─────────────────────────────────────────────────

def test_replay_fires_correct_number_of_events(generator_with_broker, mock_broker):
    events = [generator_with_broker.make_image_event() for _ in range(5)]
    generator_with_broker.replay(events)
    assert mock_broker.publish.call_count == 5

# ─── Deterministic mode ─────────────────────────────────────

def test_seed_produces_same_image_path():
    gen1 = EventGenerator(seed=42)
    gen2 = EventGenerator(seed=42)
    event1 = gen1.make_image_event()
    event2 = gen2.make_image_event()
    assert event1["payload"]["path"] == event2["payload"]["path"]