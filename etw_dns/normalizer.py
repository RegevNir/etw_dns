"""
Event normalizer for converting raw ETW events to DNS event schema.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import socket

from .schema import DNSEvent


class EventNormalizer:
    """Normalizes raw ETW events to DNSEvent schema."""
    
    def __init__(self, provider_name: str = "Microsoft-Windows-DNS-Client", 
                 provider_guid: str = "{1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}"):
        """
        Initialize event normalizer.
        
        Args:
            provider_name: ETW provider name.
            provider_guid: ETW provider GUID.
        """
        self.provider_name = provider_name
        self.provider_guid = provider_guid
        self._hostname = self._get_hostname()
    
    def normalize(self, raw_event: Dict[str, Any]) -> Optional[DNSEvent]:
        """
        Normalize raw ETW event to DNSEvent.
        
        Args:
            raw_event: Raw event dictionary from ETW provider.
            
        Returns:
            DNSEvent instance or None if event cannot be normalized.
        """
        try:
            event = DNSEvent()
            
            event.provider_name = self.provider_name
            event.provider_guid = self.provider_guid
            event.hostname = self._hostname
            
            event.timestamp = self._extract_timestamp(raw_event)
            
            event.query_name = self._extract_field(raw_event, ["QueryName", "query_name", "Name"])
            event.query_type = self._extract_field(raw_event, ["QueryType", "query_type", "Type"])
            event.status = self._extract_field(raw_event, ["QueryStatus", "query_status", "Status", "QueryResult"])
            
            event.server_ip = self._extract_field(raw_event, ["ServerIp", "server_ip", "ServerAddress"])
            event.local_addr = self._extract_field(raw_event, ["LocalAddress", "local_address", "ClientIp"])
            event.protocol = self._extract_field(raw_event, ["Protocol", "protocol"])
            
            event.pid = self._extract_int_field(raw_event, ["ProcessId", "process_id", "PID"])
            event.process_name = self._extract_field(raw_event, ["ProcessName", "process_name", "ImageName"])
            event.thread_id = self._extract_int_field(raw_event, ["ThreadId", "thread_id", "TID"])
            
            if "EventHeader" in raw_event:
                header = raw_event["EventHeader"]
                if "ActivityId" in header:
                    event.activity_id = str(header["ActivityId"])
                if "ProcessId" in header and event.pid is None:
                    event.pid = header["ProcessId"]
                if "ThreadId" in header and event.thread_id is None:
                    event.thread_id = header["ThreadId"]
            
            if event.query_name or event.query_type:
                return event
            
            return None
            
        except Exception as e:
            import sys
            print(f"Error normalizing event: {e}", file=sys.stderr)
            return None
    
    def _extract_timestamp(self, raw_event: Dict[str, Any]) -> str:
        """Extract and format timestamp from raw event."""
        timestamp = None
        
        if "EventHeader" in raw_event:
            header = raw_event["EventHeader"]
            if "TimeStamp" in header:
                timestamp = header["TimeStamp"]
        
        if timestamp is None:
            timestamp = self._extract_field(raw_event, ["TimeStamp", "timestamp", "Time"])
        
        if timestamp and isinstance(timestamp, str):
            return timestamp
        
        return datetime.now(timezone.utc).isoformat()
    
    def _extract_field(self, raw_event: Dict[str, Any], field_names: list) -> Optional[str]:
        """
        Extract field from raw event trying multiple possible field names.
        
        Args:
            raw_event: Raw event dictionary.
            field_names: List of possible field names to try.
            
        Returns:
            Field value as string or None if not found.
        """
        for name in field_names:
            if name in raw_event:
                value = raw_event[name]
                if value is not None:
                    return str(value)
        return None
    
    def _extract_int_field(self, raw_event: Dict[str, Any], field_names: list) -> Optional[int]:
        """
        Extract integer field from raw event.
        
        Args:
            raw_event: Raw event dictionary.
            field_names: List of possible field names to try.
            
        Returns:
            Field value as integer or None if not found.
        """
        for name in field_names:
            if name in raw_event:
                value = raw_event[name]
                if value is not None:
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        pass
        return None
    
    def _get_hostname(self) -> str:
        """Get local hostname."""
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"
