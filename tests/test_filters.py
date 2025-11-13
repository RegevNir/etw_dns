"""Tests for filters module."""

from etw_dns.filters import EventFilter
from etw_dns.schema import DNSEvent


def test_event_filter_no_filters():
    """Test filter with no filters configured."""
    event_filter = EventFilter()
    
    event = DNSEvent()
    event.query_name = "example.com"
    
    assert event_filter.should_include(event) is True
    assert event_filter.has_filters() is False


def test_domain_filter_exact():
    """Test exact domain filtering."""
    event_filter = EventFilter()
    event_filter.add_domain_filter("example.com")
    
    event1 = DNSEvent()
    event1.query_name = "example.com"
    
    event2 = DNSEvent()
    event2.query_name = "other.com"
    
    assert event_filter.should_include(event1) is True
    assert event_filter.should_include(event2) is False


def test_domain_filter_wildcard():
    """Test wildcard domain filtering."""
    event_filter = EventFilter()
    event_filter.add_domain_filter("*.example.com")
    
    event1 = DNSEvent()
    event1.query_name = "www.example.com"
    
    event2 = DNSEvent()
    event2.query_name = "api.example.com"
    
    event3 = DNSEvent()
    event3.query_name = "other.com"
    
    assert event_filter.should_include(event1) is True
    assert event_filter.should_include(event2) is True
    assert event_filter.should_include(event3) is False


def test_query_type_filter():
    """Test query type filtering."""
    event_filter = EventFilter()
    event_filter.add_query_type_filter(["A", "AAAA"])
    
    event1 = DNSEvent()
    event1.query_type = "A"
    
    event2 = DNSEvent()
    event2.query_type = "AAAA"
    
    event3 = DNSEvent()
    event3.query_type = "CNAME"
    
    assert event_filter.should_include(event1) is True
    assert event_filter.should_include(event2) is True
    assert event_filter.should_include(event3) is False


def test_status_filter():
    """Test status filtering."""
    event_filter = EventFilter()
    event_filter.add_status_filter(["NOERROR"])
    
    event1 = DNSEvent()
    event1.status = "NOERROR"
    
    event2 = DNSEvent()
    event2.status = "NXDOMAIN"
    
    assert event_filter.should_include(event1) is True
    assert event_filter.should_include(event2) is False


def test_process_include_filter():
    """Test process inclusion filtering."""
    event_filter = EventFilter()
    event_filter.add_process_filter(["chrome.exe", "firefox.exe"], exclude=False)
    
    event1 = DNSEvent()
    event1.process_name = "chrome.exe"
    
    event2 = DNSEvent()
    event2.process_name = "firefox.exe"
    
    event3 = DNSEvent()
    event3.process_name = "svchost.exe"
    
    assert event_filter.should_include(event1) is True
    assert event_filter.should_include(event2) is True
    assert event_filter.should_include(event3) is False


def test_process_exclude_filter():
    """Test process exclusion filtering."""
    event_filter = EventFilter()
    event_filter.add_process_filter(["svchost.exe"], exclude=True)
    
    event1 = DNSEvent()
    event1.process_name = "chrome.exe"
    
    event2 = DNSEvent()
    event2.process_name = "svchost.exe"
    
    assert event_filter.should_include(event1) is True
    assert event_filter.should_include(event2) is False


def test_pid_filter():
    """Test PID filtering."""
    event_filter = EventFilter()
    event_filter.add_pid_filter([1234, 5678], exclude=False)
    
    event1 = DNSEvent()
    event1.pid = 1234
    
    event2 = DNSEvent()
    event2.pid = 9999
    
    assert event_filter.should_include(event1) is True
    assert event_filter.should_include(event2) is False


def test_combined_filters():
    """Test multiple filters combined."""
    event_filter = EventFilter()
    event_filter.add_domain_filter("*.google.com")
    event_filter.add_query_type_filter(["A", "AAAA"])
    event_filter.add_process_filter(["chrome.exe"], exclude=False)
    
    event1 = DNSEvent()
    event1.query_name = "www.google.com"
    event1.query_type = "A"
    event1.process_name = "chrome.exe"
    
    event2 = DNSEvent()
    event2.query_name = "example.com"
    event2.query_type = "A"
    event2.process_name = "chrome.exe"
    
    event3 = DNSEvent()
    event3.query_name = "www.google.com"
    event3.query_type = "CNAME"
    event3.process_name = "chrome.exe"
    
    event4 = DNSEvent()
    event4.query_name = "www.google.com"
    event4.query_type = "A"
    event4.process_name = "firefox.exe"
    
    assert event_filter.should_include(event1) is True
    assert event_filter.should_include(event2) is False
    assert event_filter.should_include(event3) is False
    assert event_filter.should_include(event4) is False
