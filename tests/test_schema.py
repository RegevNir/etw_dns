"""Tests for schema module."""

import json
from etw_dns.schema import DNSEvent


def test_dns_event_creation():
    """Test creating a DNS event."""
    event = DNSEvent()
    assert event.schema_version == "1.0"
    assert event.tool_version == "0.1.0"


def test_dns_event_to_dict_minimal():
    """Test converting minimal event to dict."""
    event = DNSEvent()
    event.timestamp = "2025-11-13T12:00:00Z"
    event.query_name = "example.com"
    
    result = event.to_dict()
    
    assert result["schema_version"] == "1.0"
    assert result["tool_version"] == "0.1.0"
    assert result["timestamp"] == "2025-11-13T12:00:00Z"
    assert result["query_name"] == "example.com"
    assert "query_type" not in result  # Should not include None values


def test_dns_event_to_dict_complete():
    """Test converting complete event to dict."""
    event = DNSEvent()
    event.timestamp = "2025-11-13T12:00:00Z"
    event.query_name = "example.com"
    event.query_type = "A"
    event.status = "NOERROR"
    event.server_ip = "8.8.8.8"
    event.pid = 1234
    event.process_name = "chrome.exe"
    
    result = event.to_dict()
    
    assert result["query_name"] == "example.com"
    assert result["query_type"] == "A"
    assert result["status"] == "NOERROR"
    assert result["server_ip"] == "8.8.8.8"
    assert result["pid"] == 1234
    assert result["process_name"] == "chrome.exe"


def test_dns_event_to_json():
    """Test converting event to JSON string."""
    event = DNSEvent()
    event.timestamp = "2025-11-13T12:00:00Z"
    event.query_name = "example.com"
    event.query_type = "A"
    
    json_str = event.to_json()
    
    parsed = json.loads(json_str)
    assert parsed["query_name"] == "example.com"
    assert parsed["query_type"] == "A"


def test_dns_event_arrays():
    """Test event with array fields."""
    event = DNSEvent()
    event.response_ips = ["1.2.3.4", "5.6.7.8"]
    event.response_ttl = [300, 600]
    event.cname_chain = ["alias.example.com", "example.com"]
    
    result = event.to_dict()
    
    assert result["response_ips"] == ["1.2.3.4", "5.6.7.8"]
    assert result["response_ttl"] == [300, 600]
    assert result["cname_chain"] == ["alias.example.com", "example.com"]


def test_dns_event_flags():
    """Test event with DNS flags."""
    event = DNSEvent()
    event.flags = {
        "rd": True,
        "ra": True,
        "ad": False,
        "cd": False,
        "tc": False
    }
    
    result = event.to_dict()
    
    assert result["flags"]["rd"] is True
    assert result["flags"]["ra"] is True
    assert result["flags"]["ad"] is False
