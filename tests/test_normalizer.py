"""Tests for normalizer module."""

from etw_dns.normalizer import EventNormalizer


def test_normalize_minimal_event():
    """Test normalizing minimal event."""
    normalizer = EventNormalizer()
    
    raw_event = {
        "QueryName": "example.com",
        "QueryType": "A",
    }
    
    event = normalizer.normalize(raw_event)
    
    assert event is not None
    assert event.query_name == "example.com"
    assert event.query_type == "A"
    assert event.provider_name == "Microsoft-Windows-DNS-Client"


def test_normalize_complete_event():
    """Test normalizing complete event."""
    normalizer = EventNormalizer()
    
    raw_event = {
        "EventHeader": {
            "TimeStamp": "2025-11-13T12:00:00Z",
            "ProcessId": 1234,
            "ThreadId": 5678,
            "ActivityId": "12345678-1234-1234-1234-123456789abc",
        },
        "QueryName": "example.com",
        "QueryType": "A",
        "QueryStatus": "NOERROR",
        "ServerIp": "8.8.8.8",
        "ProcessName": "chrome.exe",
    }
    
    event = normalizer.normalize(raw_event)
    
    assert event is not None
    assert event.timestamp == "2025-11-13T12:00:00Z"
    assert event.query_name == "example.com"
    assert event.query_type == "A"
    assert event.status == "NOERROR"
    assert event.server_ip == "8.8.8.8"
    assert event.pid == 1234
    assert event.thread_id == 5678
    assert event.process_name == "chrome.exe"
    assert event.activity_id == "12345678-1234-1234-1234-123456789abc"


def test_normalize_alternative_field_names():
    """Test normalizing with alternative field names."""
    normalizer = EventNormalizer()
    
    raw_event = {
        "query_name": "example.com",
        "query_type": "AAAA",
        "query_status": "NOERROR",
    }
    
    event = normalizer.normalize(raw_event)
    
    assert event is not None
    assert event.query_name == "example.com"
    assert event.query_type == "AAAA"
    assert event.status == "NOERROR"


def test_normalize_missing_fields():
    """Test normalizing event with missing fields."""
    normalizer = EventNormalizer()
    
    raw_event = {
        "QueryName": "example.com",
    }
    
    event = normalizer.normalize(raw_event)
    
    assert event is not None
    assert event.query_name == "example.com"
    assert event.query_type is None
    assert event.status is None


def test_normalize_empty_event():
    """Test normalizing empty event."""
    normalizer = EventNormalizer()
    
    raw_event = {}
    
    event = normalizer.normalize(raw_event)
    
    assert event is None


def test_normalize_invalid_event():
    """Test normalizing invalid event."""
    normalizer = EventNormalizer()
    
    raw_event = None
    
    event = normalizer.normalize(raw_event)
    
    assert event is None


def test_normalize_integer_fields():
    """Test normalizing integer fields."""
    normalizer = EventNormalizer()
    
    raw_event = {
        "QueryName": "example.com",
        "ProcessId": "1234",  # String that should be converted to int
        "ThreadId": 5678,     # Already an int
    }
    
    event = normalizer.normalize(raw_event)
    
    assert event is not None
    assert event.pid == 1234
    assert event.thread_id == 5678
    assert isinstance(event.pid, int)
    assert isinstance(event.thread_id, int)
