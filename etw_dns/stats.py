"""
Statistics tracking and reporting for DNS event capture.
"""

import sys
import threading
import time
from typing import Optional


class StatsTracker:
    """Tracks and reports statistics for DNS event capture."""

    def __init__(self, report_interval: int = 10):
        """
        Initialize statistics tracker.

        Args:
            report_interval: Interval in seconds between statistics reports.
        """
        self.report_interval = report_interval
        self._events_captured = 0
        self._events_filtered = 0
        self._events_written = 0
        self._events_dropped = 0
        self._normalize_failed = 0
        self._errors = 0
        self._start_time = time.time()
        self._last_report_time = self._start_time
        self._running = False
        self._reporter_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the statistics reporter thread."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._start_time = time.time()
        self._last_report_time = self._start_time
        self._reporter_thread = threading.Thread(
            target=self._reporter_loop, daemon=True
        )
        self._reporter_thread.start()

    def stop(self) -> None:
        """Stop the statistics reporter thread."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._reporter_thread:
            self._reporter_thread.join(timeout=2.0)
            self._reporter_thread = None

        self.print_final_stats()

    def increment_captured(self) -> None:
        """Increment events captured counter."""
        with self._lock:
            self._events_captured += 1

    def increment_filtered(self) -> None:
        """Increment events filtered counter."""
        with self._lock:
            self._events_filtered += 1

    def increment_written(self) -> None:
        """Increment events written counter."""
        with self._lock:
            self._events_written += 1

    def increment_dropped(self) -> None:
        """Increment events dropped counter."""
        with self._lock:
            self._events_dropped += 1

    def increment_normalize_failed(self) -> None:
        """Increment normalization failed counter."""
        with self._lock:
            self._normalize_failed += 1

    def increment_errors(self) -> None:
        """Increment errors counter."""
        with self._lock:
            self._errors += 1

    def update_from_output_stats(self, output_stats: dict) -> None:
        """
        Update statistics from output writer stats.

        Args:
            output_stats: Statistics dictionary from OutputWriter.
        """
        with self._lock:
            self._events_written = output_stats.get("events_written", 0)
            self._events_dropped = output_stats.get("events_dropped", 0)

    def get_stats(self) -> dict:
        """
        Get current statistics.

        Returns:
            Dictionary with current statistics.
        """
        with self._lock:
            elapsed = time.time() - self._start_time
            events_per_sec = self._events_captured / elapsed if elapsed > 0 else 0

            return {
                "events_captured": self._events_captured,
                "events_filtered": self._events_filtered,
                "events_written": self._events_written,
                "events_dropped": self._events_dropped,
                "normalize_failed": self._normalize_failed,
                "errors": self._errors,
                "elapsed_seconds": elapsed,
                "events_per_second": events_per_sec,
            }

    def _reporter_loop(self) -> None:
        """Main reporter loop running in background thread."""
        while self._running:
            if self._stop_event.wait(self.report_interval):
                break

            self.print_stats()

    def print_stats(self) -> None:
        """Print current statistics to stderr."""
        stats = self.get_stats()

        current_time = time.time()
        self._last_report_time = current_time

        print(
            f"\n[Stats] Captured: {stats['events_captured']}, "
            f"Normalize failed: {stats['normalize_failed']}, "
            f"Filtered: {stats['events_filtered']}, "
            f"Written: {stats['events_written']}, "
            f"Dropped: {stats['events_dropped']}, "
            f"Errors: {stats['errors']}, "
            f"Rate: {stats['events_per_second']:.1f} events/sec",
            file=sys.stderr,
        )

    def print_final_stats(self) -> None:
        """Print final statistics to stderr."""
        stats = self.get_stats()

        normalized = stats['events_captured'] - stats['normalize_failed']
        effective_filtered = stats['events_filtered'] + stats['normalize_failed']

        print("\n" + "=" * 60, file=sys.stderr)
        print("Final Statistics:", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"Events captured:      {stats['events_captured']}", file=sys.stderr)
        print(f"Normalize failed:     {stats['normalize_failed']}", file=sys.stderr)
        print(f"Normalized:           {normalized}", file=sys.stderr)
        print(f"Events filtered:      {stats['events_filtered']}", file=sys.stderr)
        print(f"Effective filtered:   {effective_filtered}", file=sys.stderr)
        print(f"Events written:       {stats['events_written']}", file=sys.stderr)
        print(f"Events dropped:       {stats['events_dropped']}", file=sys.stderr)
        print(f"Errors:               {stats['errors']}", file=sys.stderr)
        print(
            f"Elapsed time:         {stats['elapsed_seconds']:.1f} seconds", file=sys.stderr
        )
        print(
            f"Average rate:         {stats['events_per_second']:.1f} events/sec",
            file=sys.stderr,
        )

        if stats["events_dropped"] > 0:
            drop_rate = (
                (stats["events_dropped"] / stats["events_captured"] * 100)
                if stats["events_captured"] > 0
                else 0
            )
            print(f"Drop rate:            {drop_rate:.2f}%", file=sys.stderr)

        print("=" * 60, file=sys.stderr)
