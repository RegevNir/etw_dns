"""
ETW provider interface and implementations.

Provides an abstraction layer for ETW event capture with both real and fake implementations
for testing and development on non-Windows platforms.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any
import threading


class EtwInterface(ABC):
    """Abstract interface for ETW providers."""

    @abstractmethod
    def start(self) -> None:
        """Start ETW capture session."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop ETW capture session."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if capture is running."""
        pass


class RealEtwProvider(EtwInterface):
    """
    Real ETW provider using pywintrace library.

    This implementation subscribes to the Microsoft-Windows-DNS-Client ETW provider
    and processes DNS events in real-time.
    """

    DNS_CLIENT_GUID = "{1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}"
    DNS_CLIENT_NAME = "Microsoft-Windows-DNS-Client"

    def __init__(self, event_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize real ETW provider.

        Args:
            event_callback: Callback function to process each ETW event.
        """
        self.event_callback = event_callback
        self._running = False
        self._etw_instance = None

        try:
            import etw

            self._etw_module = etw
        except ImportError:
            raise ImportError(
                "pywintrace library not found. "
                "Install it with: pip install git+https://github.com/fireeye/pywintrace@v0.3.0"
            )

    def start(self) -> None:
        """Start ETW capture session."""
        if self._running:
            return

        providers = [
            self._etw_module.ProviderInfo(
                self.DNS_CLIENT_NAME, self._etw_module.GUID(self.DNS_CLIENT_GUID)
            )
        ]

        self._etw_instance = self._etw_module.ETW(
            providers=providers, event_callback=self._on_etw_event
        )

        self._etw_instance.start()
        self._running = True

    def stop(self) -> None:
        """Stop ETW capture session."""
        if not self._running:
            return

        if self._etw_instance:
            self._etw_instance.stop()
            self._etw_instance = None

        self._running = False

    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._running

    def _on_etw_event(self, event: Any) -> None:
        """
        Internal callback for ETW events.

        This method receives raw ETW events and converts them to dictionaries
        before passing to the user callback.

        Args:
            event: Raw ETW event from pywintrace.
        """
        try:
            event_dict = self._convert_etw_event(event)

            self.event_callback(event_dict)
        except Exception as e:
            import sys

            print(f"Error processing ETW event: {e}", file=sys.stderr)

    def _convert_etw_event(self, event: Any) -> Dict[str, Any]:
        """
        Convert raw ETW event to dictionary.

        Args:
            event: Raw ETW event from pywintrace.

        Returns:
            Dictionary representation of the event.
        """

        event_dict = {}

        try:
            if hasattr(event, "__dict__"):
                event_dict = dict(event.__dict__)
            elif isinstance(event, dict):
                event_dict = dict(event)
            else:
                event_dict = {"raw_event": str(event)}
        except Exception:
            event_dict = {"raw_event": str(event)}

        return event_dict


class FakeEtwProvider(EtwInterface):
    """
    Fake ETW provider for testing and development on non-Windows platforms.

    This implementation generates synthetic DNS events for testing purposes.
    """

    def __init__(self, event_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize fake ETW provider.

        Args:
            event_callback: Callback function to process each synthetic event.
        """
        self.event_callback = event_callback
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start generating synthetic events."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._generate_events, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop generating synthetic events."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def is_running(self) -> bool:
        """Check if generation is running."""
        return self._running

    def _generate_events(self) -> None:
        """Generate synthetic DNS events for testing."""
        import random
        from datetime import datetime, timezone

        domains = [
            "example.com",
            "google.com",
            "github.com",
            "microsoft.com",
            "stackoverflow.com",
        ]

        query_types = ["A", "AAAA", "CNAME", "PTR", "TXT"]
        statuses = ["NOERROR", "NXDOMAIN", "SERVFAIL"]
        processes = ["chrome.exe", "firefox.exe", "python.exe", "curl.exe"]

        event_id = 0

        while not self._stop_event.is_set():
            event_id += 1

            event = {
                "EventHeader": {
                    "TimeStamp": datetime.now(timezone.utc).isoformat(),
                    "ProcessId": random.randint(1000, 9999),
                    "ThreadId": random.randint(100, 999),
                    "ActivityId": f"{event_id:08x}-0000-0000-0000-000000000000",
                },
                "QueryName": random.choice(domains),
                "QueryType": random.choice(query_types),
                "QueryStatus": random.choice(statuses),
                "ServerIp": f"8.8.{random.randint(1, 8)}.{random.randint(1, 8)}",
                "ProcessName": random.choice(processes),
            }

            try:
                self.event_callback(event)
            except Exception as e:
                import sys

                print(f"Error in fake event callback: {e}", file=sys.stderr)

            self._stop_event.wait(0.1)


def create_etw_provider(
    event_callback: Callable[[Dict[str, Any]], None], use_fake: bool = False
) -> EtwInterface:
    """
    Factory function to create appropriate ETW provider.

    Args:
        event_callback: Callback function to process events.
        use_fake: If True, use fake provider for testing.

    Returns:
        ETW provider instance.
    """
    if use_fake:
        return FakeEtwProvider(event_callback)
    else:
        return RealEtwProvider(event_callback)
