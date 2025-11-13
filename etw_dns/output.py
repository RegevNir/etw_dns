"""
Output writer for DNS events.
"""

from typing import Optional, TextIO
import sys
import threading
from queue import Queue, Full
import time

from .schema import DNSEvent


class OutputWriter:
    """Writes DNS events to output in JSONL format."""
    
    def __init__(self, output_file: Optional[str] = None, queue_size: int = 10000):
        """
        Initialize output writer.
        
        Args:
            output_file: Path to output file, or None for stdout.
            queue_size: Maximum size of event queue.
        """
        self.output_file = output_file
        self.queue_size = queue_size
        self._queue: Queue = Queue(maxsize=queue_size)
        self._file_handle: Optional[TextIO] = None
        self._writer_thread: Optional[threading.Thread] = None
        self._running = False
        self._stop_event = threading.Event()
        self._events_written = 0
        self._events_dropped = 0
    
    def start(self) -> None:
        """Start the output writer thread."""
        if self._running:
            return
        
        if self.output_file:
            try:
                self._file_handle = open(self.output_file, 'a', encoding='utf-8')
            except Exception as e:
                print(f"Error opening output file: {e}", file=sys.stderr)
                sys.exit(4)
        else:
            self._file_handle = sys.stdout
        
        self._running = True
        self._stop_event.clear()
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()
    
    def stop(self) -> None:
        """Stop the output writer thread and flush remaining events."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._writer_thread:
            self._writer_thread.join(timeout=5.0)
            self._writer_thread = None
        
        self._flush_remaining()
        
        if self._file_handle and self._file_handle != sys.stdout:
            self._file_handle.close()
            self._file_handle = None
    
    def write_event(self, event: DNSEvent) -> bool:
        """
        Queue an event for writing.
        
        Args:
            event: DNS event to write.
            
        Returns:
            True if event was queued, False if queue is full (event dropped).
        """
        try:
            self._queue.put_nowait(event)
            return True
        except Full:
            self._events_dropped += 1
            return False
    
    def get_stats(self) -> dict:
        """
        Get output statistics.
        
        Returns:
            Dictionary with statistics.
        """
        return {
            "events_written": self._events_written,
            "events_dropped": self._events_dropped,
            "queue_size": self._queue.qsize(),
        }
    
    def _writer_loop(self) -> None:
        """Main writer loop running in background thread."""
        while self._running or not self._queue.empty():
            try:
                event = self._queue.get(timeout=0.1)
                self._write_event(event)
            except Exception:
                continue
    
    def _write_event(self, event: DNSEvent) -> None:
        """
        Write a single event to output.
        
        Args:
            event: DNS event to write.
        """
        try:
            json_line = event.to_json()
            if self._file_handle:
                self._file_handle.write(json_line)
                self._file_handle.write('\n')
                self._file_handle.flush()
                self._events_written += 1
        except Exception as e:
            print(f"Error writing event: {e}", file=sys.stderr)
    
    def _flush_remaining(self) -> None:
        """Flush any remaining events in the queue."""
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                self._write_event(event)
            except Exception:
                break
