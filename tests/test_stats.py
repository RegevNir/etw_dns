"""Tests for statistics tracking."""

import pytest
from etw_dns.stats import StatsTracker


def test_stats_tracker_initialization():
    """Test that StatsTracker initializes with zero counters."""
    tracker = StatsTracker(report_interval=10)
    stats = tracker.get_stats()
    
    assert stats["events_captured"] == 0
    assert stats["events_filtered"] == 0
    assert stats["events_written"] == 0
    assert stats["events_dropped"] == 0
    assert stats["normalize_failed"] == 0
    assert stats["errors"] == 0


def test_stats_tracker_increment_captured():
    """Test incrementing captured counter."""
    tracker = StatsTracker(report_interval=10)
    
    tracker.increment_captured()
    tracker.increment_captured()
    
    stats = tracker.get_stats()
    assert stats["events_captured"] == 2


def test_stats_tracker_increment_normalize_failed():
    """Test incrementing normalize_failed counter."""
    tracker = StatsTracker(report_interval=10)
    
    tracker.increment_normalize_failed()
    tracker.increment_normalize_failed()
    tracker.increment_normalize_failed()
    
    stats = tracker.get_stats()
    assert stats["normalize_failed"] == 3


def test_stats_tracker_normalization_failure_scenario():
    """Test statistics when events fail normalization."""
    tracker = StatsTracker(report_interval=10)
    
    tracker.increment_captured()
    tracker.increment_captured()
    tracker.increment_captured()
    tracker.increment_normalize_failed()
    tracker.increment_normalize_failed()
    tracker.increment_filtered()
    
    stats = tracker.get_stats()
    
    assert stats["events_captured"] == 3
    assert stats["normalize_failed"] == 2
    assert stats["events_filtered"] == 1
    assert stats["events_written"] == 0


def test_stats_tracker_all_filtered_scenario():
    """Test statistics when all events are filtered out."""
    tracker = StatsTracker(report_interval=10)
    
    for _ in range(78):
        tracker.increment_captured()
    
    for _ in range(2):
        tracker.increment_normalize_failed()
    
    for _ in range(76):
        tracker.increment_filtered()
    
    stats = tracker.get_stats()
    
    assert stats["events_captured"] == 78
    assert stats["normalize_failed"] == 2
    assert stats["events_filtered"] == 76
    assert stats["events_written"] == 0
    
    normalized = stats["events_captured"] - stats["normalize_failed"]
    effective_filtered = stats["events_filtered"] + stats["normalize_failed"]
    
    assert normalized == 76
    assert effective_filtered == 78


def test_stats_tracker_mixed_scenario():
    """Test statistics with mixed outcomes."""
    tracker = StatsTracker(report_interval=10)
    
    for _ in range(100):
        tracker.increment_captured()
    
    tracker.increment_normalize_failed()
    tracker.increment_normalize_failed()
    
    for _ in range(20):
        tracker.increment_filtered()
    
    for _ in range(75):
        tracker.increment_written()
    
    for _ in range(3):
        tracker.increment_dropped()
    
    stats = tracker.get_stats()
    
    assert stats["events_captured"] == 100
    assert stats["normalize_failed"] == 2
    assert stats["events_filtered"] == 20
    assert stats["events_written"] == 75
    assert stats["events_dropped"] == 3
    
    normalized = stats["events_captured"] - stats["normalize_failed"]
    assert normalized == 98
    assert normalized == stats["events_filtered"] + stats["events_written"] + stats["events_dropped"]
