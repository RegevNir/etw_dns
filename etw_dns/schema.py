"""
Schema definitions for DNS event output.
"""

from typing import Dict, List, Optional, Any
import json

from .version import SCHEMA_VERSION, VERSION


class DNSEvent:
    """Represents a DNS event with all captured fields."""

    def __init__(self):
        self.schema_version = SCHEMA_VERSION
        self.tool_version = VERSION
        self.timestamp: Optional[str] = None
        self.event_type: Optional[str] = None

        self.query_name: Optional[str] = None
        self.query_type: Optional[str] = None
        self.status: Optional[str] = None
        self.latency_ms: Optional[int] = None

        self.server_ip: Optional[str] = None
        self.local_addr: Optional[str] = None
        self.protocol: Optional[str] = None
        self.transport_port: Optional[int] = None

        self.response_ips: List[str] = []
        self.response_ttl: List[int] = []
        self.cname_chain: List[str] = []

        self.flags: Dict[str, bool] = {}

        self.pid: Optional[int] = None
        self.process_name: Optional[str] = None
        self.process_path: Optional[str] = None
        self.command_line: Optional[str] = None

        self.activity_id: Optional[str] = None
        self.thread_id: Optional[int] = None

        self.hostname: Optional[str] = None
        self.user: Optional[str] = None

        self.provider_name: Optional[str] = None
        self.provider_guid: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary, excluding None values."""
        result = {
            "schema_version": self.schema_version,
            "tool_version": self.tool_version,
        }

        if self.timestamp:
            result["timestamp"] = self.timestamp
        if self.event_type:
            result["event_type"] = self.event_type

        if self.query_name:
            result["query_name"] = self.query_name
        if self.query_type:
            result["query_type"] = self.query_type
        if self.status:
            result["status"] = self.status
        if self.latency_ms is not None:
            result["latency_ms"] = self.latency_ms

        if self.server_ip:
            result["server_ip"] = self.server_ip
        if self.local_addr:
            result["local_addr"] = self.local_addr
        if self.protocol:
            result["protocol"] = self.protocol
        if self.transport_port is not None:
            result["transport_port"] = self.transport_port

        if self.response_ips:
            result["response_ips"] = self.response_ips
        if self.response_ttl:
            result["response_ttl"] = self.response_ttl
        if self.cname_chain:
            result["cname_chain"] = self.cname_chain

        if self.flags:
            result["flags"] = self.flags

        if self.pid is not None:
            result["pid"] = self.pid
        if self.process_name:
            result["process_name"] = self.process_name
        if self.process_path:
            result["process_path"] = self.process_path
        if self.command_line:
            result["command_line"] = self.command_line

        if self.activity_id:
            result["activity_id"] = self.activity_id
        if self.thread_id is not None:
            result["thread_id"] = self.thread_id

        if self.hostname:
            result["hostname"] = self.hostname
        if self.user:
            result["user"] = self.user

        if self.provider_name:
            result["provider_name"] = self.provider_name
        if self.provider_guid:
            result["provider_guid"] = self.provider_guid

        return result

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
