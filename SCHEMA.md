# ETW DNS Event Schema

This document describes the output schema for DNS events captured by the ETW DNS tool.

## Format

Events are output in **JSONL (JSON Lines)** format, with one JSON object per line. Each line is a complete, valid JSON object.

## Schema Version

Current schema version: **1.0**

The `schema_version` field in each event indicates the schema version, allowing for future schema evolution while maintaining backward compatibility.

## Field Reference

### Metadata Fields

These fields are present in every event:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | Yes | Schema version (currently "1.0") |
| `tool_version` | string | Yes | Tool version that generated the event |
| `timestamp` | string | Yes | Event timestamp in ISO 8601 format (UTC) |
| `provider_name` | string | Yes | ETW provider name (e.g., "Microsoft-Windows-DNS-Client") |
| `provider_guid` | string | Yes | ETW provider GUID |
| `hostname` | string | Yes | Local hostname where capture is running |

### Core DNS Fields

These fields contain the primary DNS query information:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query_name` | string | No | DNS query domain name (e.g., "example.com") |
| `query_type` | string | No | DNS query type (e.g., "A", "AAAA", "CNAME", "PTR", "TXT") |
| `status` | string | No | Query result status (e.g., "NOERROR", "NXDOMAIN", "SERVFAIL") |
| `event_type` | string | No | Event type (e.g., "query_complete", "query_start") |
| `latency_ms` | integer | No | Query latency in milliseconds (if available) |

### Network Context Fields

These fields provide network-level context:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_ip` | string | No | DNS server IP address |
| `local_addr` | string | No | Local interface IP address |
| `protocol` | string | No | Transport protocol ("UDP" or "TCP") |
| `transport_port` | integer | No | Transport port number |
| `response_ips` | array[string] | No | Array of IP addresses in DNS response |
| `response_ttl` | array[integer] | No | Array of TTL values for responses |
| `cname_chain` | array[string] | No | CNAME resolution chain |

### DNS Flags

DNS protocol flags (if available):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flags` | object | No | DNS flags object |
| `flags.rd` | boolean | No | Recursion Desired |
| `flags.ra` | boolean | No | Recursion Available |
| `flags.ad` | boolean | No | Authenticated Data |
| `flags.cd` | boolean | No | Checking Disabled |
| `flags.tc` | boolean | No | Truncated |

### Process Context Fields

These fields provide information about the process that initiated the DNS query:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pid` | integer | No | Process ID |
| `process_name` | string | No | Process executable name (e.g., "chrome.exe") |
| `process_path` | string | No | Full path to process executable |
| `command_line` | string | No | Process command line arguments |

### Correlation Fields

These fields help correlate related events:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activity_id` | string | No | ETW activity/correlation ID (GUID format) |
| `thread_id` | integer | No | Thread ID that initiated the query |
| `user` | string | No | Username (if available) |

## Field Availability

**Important:** Not all fields are available in every event. Field availability depends on:

- The ETW provider's event schema
- The Windows version
- The specific event type
- Whether the information is accessible at capture time

Fields that are not available or not applicable are **omitted** from the JSON output (not set to `null`).

## Sample Events

### Minimal Event

A minimal event with only required and core fields:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.1.0",
  "timestamp": "2025-11-13T12:00:00.123456Z",
  "query_name": "example.com",
  "query_type": "A",
  "status": "NOERROR",
  "hostname": "WORKSTATION01",
  "provider_name": "Microsoft-Windows-DNS-Client",
  "provider_guid": "{1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}"
}
```

### Complete Event

A complete event with all available fields:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.1.0",
  "timestamp": "2025-11-13T12:00:00.123456Z",
  "event_type": "query_complete",
  "query_name": "www.example.com",
  "query_type": "A",
  "status": "NOERROR",
  "latency_ms": 45,
  "response_ips": ["93.184.216.34"],
  "response_ttl": [86400],
  "server_ip": "8.8.8.8",
  "local_addr": "192.168.1.100",
  "protocol": "UDP",
  "transport_port": 53,
  "flags": {
    "rd": true,
    "ra": true,
    "ad": false,
    "cd": false,
    "tc": false
  },
  "pid": 1234,
  "process_name": "chrome.exe",
  "process_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "activity_id": "12345678-1234-1234-1234-123456789abc",
  "thread_id": 5678,
  "hostname": "WORKSTATION01",
  "provider_name": "Microsoft-Windows-DNS-Client",
  "provider_guid": "{1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}"
}
```

### NXDOMAIN Event

An event for a non-existent domain:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.1.0",
  "timestamp": "2025-11-13T12:00:01.234567Z",
  "query_name": "nonexistent.example.com",
  "query_type": "A",
  "status": "NXDOMAIN",
  "server_ip": "8.8.8.8",
  "pid": 1234,
  "process_name": "chrome.exe",
  "hostname": "WORKSTATION01",
  "provider_name": "Microsoft-Windows-DNS-Client",
  "provider_guid": "{1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}"
}
```

### AAAA Query Event

An IPv6 address query:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.1.0",
  "timestamp": "2025-11-13T12:00:02.345678Z",
  "query_name": "ipv6.example.com",
  "query_type": "AAAA",
  "status": "NOERROR",
  "response_ips": ["2001:db8::1"],
  "response_ttl": [3600],
  "server_ip": "2001:4860:4860::8888",
  "protocol": "UDP",
  "pid": 2345,
  "process_name": "firefox.exe",
  "hostname": "WORKSTATION01",
  "provider_name": "Microsoft-Windows-DNS-Client",
  "provider_guid": "{1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}"
}
```

## Query Types

Common DNS query types you may encounter:

- `A` - IPv4 address
- `AAAA` - IPv6 address
- `CNAME` - Canonical name (alias)
- `PTR` - Pointer (reverse DNS)
- `TXT` - Text record
- `MX` - Mail exchange
- `NS` - Name server
- `SOA` - Start of authority
- `SRV` - Service locator

## Status Codes

Common DNS status codes:

- `NOERROR` - Successful query
- `NXDOMAIN` - Non-existent domain
- `SERVFAIL` - Server failure
- `REFUSED` - Query refused
- `FORMERR` - Format error
- `NOTIMPL` - Not implemented

## Processing JSONL Output

### Python Example

```python
import json

with open('dns_events.jsonl', 'r') as f:
    for line in f:
        event = json.loads(line)
        print(f"{event['timestamp']}: {event.get('query_name')} -> {event.get('status')}")
```

### PowerShell Example

```powershell
Get-Content dns_events.jsonl | ForEach-Object {
    $event = $_ | ConvertFrom-Json
    Write-Host "$($event.timestamp): $($event.query_name) -> $($event.status)"
}
```

### jq Example

```bash
# Extract all query names
jq -r '.query_name' dns_events.jsonl

# Filter by status
jq 'select(.status == "NXDOMAIN")' dns_events.jsonl

# Count queries by type
jq -r '.query_type' dns_events.jsonl | sort | uniq -c
```

## Schema Evolution

Future versions of the tool may add new fields or modify the schema. The `schema_version` field allows consumers to handle different schema versions appropriately.

When the schema changes:
- The `schema_version` will be incremented
- New fields will be added (never removed)
- Existing field semantics will remain compatible
- Deprecated fields will be documented but maintained for backward compatibility

## Limitations

### DoH/DoT Visibility

DNS over HTTPS (DoH) and DNS over TLS (DoT) queries may not be fully visible through the Microsoft-Windows-DNS-Client ETW provider, as these protocols may bypass traditional DNS client APIs.

### Process Information

Process information (PID, process name, etc.) is best-effort and may not always be available:
- The process may have exited by the time the event is processed
- Some system processes may not expose this information
- Permissions may prevent access to process details

### Field Accuracy

Field availability and accuracy depend on the ETW provider implementation and may vary across Windows versions. Always validate critical data and handle missing fields gracefully.
