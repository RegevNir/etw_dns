"""
HTTP ingestion module for sending DNS events to remote API.
"""

import json
import time
import threading
import sys
from typing import Dict, Any, List, Optional
from queue import Queue, Empty
import urllib.request
import urllib.error


class HttpIngestor:
    """Handles HTTP ingestion of DNS events to remote API."""

    def __init__(
        self,
        ingest_url: str,
        api_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 5.0,
    ):
        """
        Initialize HTTP ingestor.

        Args:
            ingest_url: URL of the ingestion API endpoint.
            api_key: Optional API key for authentication.
            batch_size: Number of events to batch before sending.
            flush_interval: Time in seconds between flushes.
        """
        self.ingest_url = ingest_url
        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self.queue: Queue = Queue()
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None

        self.stats_lock = threading.Lock()
        self.events_sent = 0
        self.events_failed = 0
        self.batches_sent = 0
        self.batches_failed = 0

    def start(self) -> None:
        """Start the HTTP ingestor worker thread."""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def stop(self) -> None:
        """Stop the HTTP ingestor and flush remaining events."""
        if not self.running:
            return

        self.running = False

        if self.worker_thread:
            self.worker_thread.join(timeout=10)

    def enqueue_event(self, event: Dict[str, Any]) -> None:
        """
        Add an event to the ingestion queue.

        Args:
            event: Normalized DNS event.
        """
        if self.running:
            transformed = self._transform_event(event)
            self.queue.put(transformed)
    
    def _transform_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform etw_dns event format to backend API format.
        
        Args:
            event: Event in etw_dns format.
            
        Returns:
            Event in backend API format.
        """
        return {
            "query_name": event.get("query_name"),
            "query_type": event.get("query_type"),
            "query_status": event.get("status"),
            "timestamp": event.get("timestamp"),
            "process_name": event.get("process_name"),
            "process_id": event.get("pid"),
            "server_ip": event.get("server_ip"),
            "client_ip": event.get("local_addr"),
            "response_ips": event.get("response_ips", []),
            "ttl": event.get("response_ttl", [None])[0] if event.get("response_ttl") else None,
        }

    def get_stats(self) -> Dict[str, int]:
        """
        Get ingestion statistics.

        Returns:
            Dictionary with stats compatible with StatsTracker.
        """
        with self.stats_lock:
            return {
                "events_written": self.events_sent,
                "events_dropped": self.events_failed,
                "batches_sent": self.batches_sent,
                "batches_failed": self.batches_failed,
            }

    def _worker(self) -> None:
        """Worker thread that batches and sends events."""
        batch: List[Dict[str, Any]] = []
        last_flush = time.time()

        while self.running:
            try:
                timeout = max(0.1, self.flush_interval - (time.time() - last_flush))
                event = self.queue.get(timeout=timeout)
                batch.append(event)

                should_flush = (
                    len(batch) >= self.batch_size
                    or (time.time() - last_flush) >= self.flush_interval
                )

                if should_flush:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()

            except Empty:
                if batch and (time.time() - last_flush) >= self.flush_interval:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()

        if batch:
            self._send_batch(batch)

    def _send_batch(self, batch: List[Dict[str, Any]]) -> None:
        """
        Send a batch of events to the API.

        Args:
            batch: List of events to send.
        """
        if not batch:
            return

        try:
            payload = {"events": batch}
            data = json.dumps(payload).encode("utf-8")

            headers = {
                "Content-Type": "application/json",
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            req = urllib.request.Request(
                self.ingest_url, data=data, headers=headers, method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    with self.stats_lock:
                        self.events_sent += len(batch)
                        self.batches_sent += 1
                else:
                    with self.stats_lock:
                        self.events_failed += len(batch)
                        self.batches_failed += 1

        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            print(f"[HTTP Ingestor] Error sending batch: {e}", file=sys.stderr)
            with self.stats_lock:
                self.events_failed += len(batch)
                self.batches_failed += 1
