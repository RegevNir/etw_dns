# Product Requirements Document: ETW DNS Live Capture Tool

## 1. Overview and Goals

Build a Windows-only Python CLI tool that subscribes to ETW (Event Tracing for Windows) DNS providers to capture live DNS resolution activity in real time and emit structured records suitable for analysis, troubleshooting, and enrichment.

**Primary Goal:** Provide reliable, low-overhead, near-real-time DNS query/response telemetry from Windows endpoints.

**Secondary Goal:** Offer basic filtering, output to file/STDOUT, and simple enrichment (process info, latency) where available.

## 2. Target Users and Use Cases

**Security Analysts and Incident Responders**
- Trace suspicious domains and correlate to processes
- Investigate potential data exfiltration or C2 communications
- Build timeline of DNS activity during incident response

**Network/SRE/Helpdesk Teams**
- Troubleshoot resolution failures and latency issues
- Debug DNS misconfiguration
- Monitor DNS server performance

**Data Engineering/Observability Teams**
- Feed JSONL into SIEM/log pipelines for correlation
- Build DNS analytics dashboards
- Integrate with existing observability stack

## 3. Platform and Technical Requirements

### Operating System Support
- **Primary:** Windows 10 and Windows 11 (x64)
- **Secondary:** Windows Server 2019+ (preferred)
- **Best Effort:** Windows Server 2016 (if provider schema matches)

### Python Version
- Python 3.10+ (exact version to be confirmed)

### Privileges
- **Administrative rights required** to start/enable ETW real-time sessions
- Tool must detect privilege level and fail gracefully with clear guidance if not running as admin

### ETW Providers
- **Default Provider:** `Microsoft-Windows-DNS-Client` (for endpoint query visibility)
- **Optional/Future:** `Microsoft-Windows-DNS-Server` (server-side capture)
- **Note:** Exact provider GUIDs, event IDs, and field names to be confirmed from Windows manifests

### Runtime Mode
- **Primary:** Real-time subscription to live ETW events
- **Future/Optional:** Ingest offline ETL traces (out of scope for MVP unless requested)

## 4. Functional Requirements

### 4.1 Event Capture

The tool shall subscribe to the DNS client ETW provider in real time and capture the following fields when available from the provider:

**Core Fields:**
- `timestamp` - Event timestamp
- `event_type` - Query start/stop or completion
- `query_name` - DNS query domain name
- `query_type` - Record type (A, AAAA, CNAME, PTR, TXT, etc.)
- `status` - Query result (NOERROR, NXDOMAIN, SERVFAIL, etc.)
- `latency_ms` - Computed from start/stop pairs if available

**Network Context:**
- `server_ip` - DNS server IP address
- `local_addr` - Local interface address
- `protocol` - UDP or TCP
- `transport_port` - Port number
- `response_ips[]` - Array of resolved IP addresses
- `response_ttl[]` - TTL values for responses
- `cname_chain[]` - CNAME resolution chain if applicable

**DNS Flags:**
- `rd` - Recursion Desired
- `ra` - Recursion Available
- `ad` - Authenticated Data
- `cd` - Checking Disabled
- `tc` - Truncated

**Process Context Enrichment:**
- `pid` - Process ID
- `process_name` - Process executable name
- `process_path` - Full executable path (optional)
- `command_line` - Command line arguments (optional)

**Correlation:**
- `activity_id` - ETW activity/correlation ID
- `thread_id` - Thread ID

**Host Metadata:**
- `hostname` - Local hostname
- `user` - Username (optional)

**Tool Metadata:**
- `schema_version` - Output schema version
- `tool_version` - etw_dns version
- `provider_name` - ETW provider name
- `provider_guid` - ETW provider GUID

**Note:** Actual field availability depends on the provider manifest. The tool should include only fields present in events and log when expected fields are missing.

### 4.2 Filtering

Support filtering by:
- Domain suffix/pattern (e.g., `*.corp.local`)
- Query type (A, AAAA, CNAME, etc.)
- Status/result code
- PID or process name
- DNS server IP
- Local interface
- Include/exclude lists for domains and processes

### 4.3 Output Formats

**Primary Format: JSONL (JSON Lines)**
- One JSON object per line
- Stable schema with versioning
- Include `schema_version` field in each event
- Default to STDOUT; option to write to file

**Secondary Format: CSV**
- Optional CSV output for compatibility
- Flattened schema with essential fields

**Output Options:**
- Write to STDOUT (default)
- Write to file with path specification
- Size-based and time-based log rotation
- Configurable rotation policies

### 4.4 CLI Controls

Command-line flags for:
- Filter configuration (domain, type, status, PID, process)
- Output format (JSONL, CSV)
- Output destination (STDOUT, file path)
- Log level (DEBUG, INFO, WARNING, ERROR)
- Provider selection
- Anonymization settings
- Statistics reporting interval
- Configuration file path (optional YAML/JSON)

**Graceful Shutdown:**
- Handle Ctrl+C signal
- Disable ETW provider cleanly
- Stop trace session properly
- Flush buffered events
- Report final statistics

### 4.5 Observability

**Runtime Statistics (to STDERR or log):**
- Events captured per second
- Events queued
- Events written
- Events dropped
- Error count
- Configurable reporting interval (default: every 10 seconds)

### 4.6 Configuration

- **Primary:** CLI arguments
- **Optional:** YAML or JSON configuration file
- Configuration file can specify all CLI options
- CLI arguments override config file settings

## 5. Non-Functional Requirements

### 5.1 Performance
- Sustain at least **5,000 events/minute** with <5% event loss
- CPU usage <5% on typical workstation under normal load
- Memory usage <200MB during continuous operation
- Non-blocking event callbacks with internal queue
- Dedicated writer thread for output

### 5.2 Reliability
- No crashes on malformed or unexpected event payloads
- Defensive parsing with error handling
- Retries and guards around ETW API calls
- Continuous operation for 24+ hours without memory leaks
- Graceful degradation when optional fields unavailable

### 5.3 Security and Privacy

**Privilege Management:**
- Run only with user consent and administrative privileges
- Clear error messages when privileges insufficient

**Data Privacy:**
- Optional hashing/anonymization of `query_name` and `process_path`
- User-provided salt for hashing
- Configurable anonymization toggles
- Documented data retention policies

**Security Best Practices:**
- No credential logging
- Secure handling of sensitive data
- Input validation and sanitization

### 5.4 Compatibility
- Tolerate minor schema changes across Windows versions
- Defensive parsing with feature flags
- Version detection and schema adaptation
- Document tested Windows versions

### 5.5 Diagnostics
- Structured internal logging
- `--debug-etw` mode to show raw ETW field names
- Detailed error messages with troubleshooting guidance
- Event loss tracking and reporting

## 6. Dependencies and Libraries

### 6.1 Python ETW Libraries (To Evaluate)

Options to consider:
- `python-etw` - Python ETW wrapper
- `etw` - Alternative ETW binding
- `pywintrace` - PyWin32-based wrapper
- Custom wrapper using `pywin32`

**Evaluation Criteria:**
- Active maintenance status
- Real-time subscription support
- Performance characteristics
- Documentation quality
- Community adoption

**Fallback Approach:**
If Python wrappers prove insufficient, consider a small C#/.NET helper using TraceEvent or KrabsETW that pipes events to Python. Keep Python-only for MVP unless blockers arise.

### 6.2 Dependency Management
- Pin all versions in `requirements.txt` or `pyproject.toml`
- Document installation steps
- Windows-only dependency set
- Clear documentation of system requirements

## 7. CLI Design

### Example Usage

```bash
# Basic capture to STDOUT
python etw_dns.py

# Capture with filtering and file output
python etw_dns.py --format jsonl --out logs.jsonl \
  --filter-domain "*.corp.local" \
  --filter-type A,AAAA \
  --include-process chrome.exe \
  --stats-interval 10

# Capture with anonymization
python etw_dns.py --anonymize --anonymize-salt "my-secret-salt" \
  --out secure-logs.jsonl

# Debug mode
python etw_dns.py --debug-etw --log-level DEBUG
```

### Exit Codes
- `0` - Success
- `1` - General error
- `2` - Elevation/privileges required
- `3` - ETW provider failure
- `4` - Invalid output path or configuration
- `5` - Unsupported Windows version

## 8. Data Model

### Sample JSONL Event

```json
{
  "schema_version": "1.0",
  "tool_version": "0.1.0",
  "timestamp": "2025-11-13T11:00:00.123Z",
  "event_type": "query_complete",
  "query_name": "example.com",
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
  "hostname": "WORKSTATION01",
  "provider_name": "Microsoft-Windows-DNS-Client",
  "provider_guid": "{1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}"
}
```

**Note:** Actual field availability depends on ETW provider manifest. Missing fields will be omitted from output.

## 9. Deliverables

### Code
- `etw_dns.py` - Main CLI tool with real-time ETW subscription
- Modular architecture with separation of concerns
- Clean, documented, maintainable code

### Documentation
- `README.md` - Installation, usage, and examples
- `SCHEMA.md` - Output schema documentation with sample events
- `VALIDATION.md` - Manual validation guide for Windows hosts
- Provider enumeration commands and sample output

### Testing
- Unit tests for schema validation
- Unit tests for CLI argument parsing
- Unit tests for filtering logic
- Windows CI workflow (GitHub Actions) for lint and tests
- Manual validation checklist

### Packaging
- `requirements.txt` or `pyproject.toml` with pinned dependencies
- Installation instructions
- Version management

### Optional
- Example PowerShell scripts for JSONL analysis
- Sample dashboard queries
- Integration examples (SIEM, log aggregators)

## 10. Out of Scope (MVP)

The following are explicitly **not included** in the initial release:

- Offline ETL file parsing
- Kernel-mode or raw packet capture (pcap)
- Deep DNS protocol decoding beyond ETW-exposed fields
- Full DoH (DNS over HTTPS) visibility (see limitations below)
- DoT (DNS over TLS) visibility
- Endpoint deployment tooling (SCCM/Intune packaging)
- GUI interface
- Real-time alerting or rule engine
- Database storage integration
- Distributed deployment management

## 11. Risks and Mitigations

### ETW Library Stability
**Risk:** Python ETW libraries may be unmaintained or have limited functionality.
**Mitigation:** Create abstraction layer for ETW interaction. Evaluate multiple libraries. Plan fallback to C#/.NET helper if needed.

### Event Volume Spikes
**Risk:** High DNS query rates could cause event drops.
**Mitigation:** Non-blocking callbacks with bounded queues. Backpressure metrics. Document performance limits. Implement flow control.

### Provider Schema Variance
**Risk:** ETW provider schemas vary across Windows versions.
**Mitigation:** Detect provider version. Guard parsing with try/catch. Document tested versions. Feature flags for version-specific fields.

### Privilege Requirements
**Risk:** Users may not understand admin requirement.
**Mitigation:** Clear privilege detection. Helpful error messages. Documentation with elevation guidance.

### Privacy Compliance
**Risk:** Captured DNS data may contain sensitive information.
**Mitigation:** Provide anonymization toggles. Document data handling. Default to no anonymization with clear opt-in. Include retention policy guidance.

### DoH/DoT Limitations
**Risk:** DNS over HTTPS may not surface queries via DNS-Client ETW.
**Mitigation:** Document this limitation explicitly. Note as known constraint. Consider future enhancement to detect DoH usage.

### Development Environment
**Risk:** Development on Linux cannot run or validate ETW functionality.
**Mitigation:** Plan for Windows-side manual validation. Include validation guide. Consider Windows VM or CI for testing.

## 12. Acceptance Criteria

The MVP is considered complete when:

1. **Basic Functionality:** On a Windows 10/11 test machine, the tool captures live DNS queries for A/AAAA lookups and emits JSONL with at minimum: `timestamp`, `query_name`, `query_type`, `status`, `pid`, `process_name`, and `server_ip` (when available).

2. **Filtering:** Successfully demonstrates filtering by domain suffix and process name.

3. **Stability:** Runs for 5+ minutes with no crashes and <5% event loss at sustained test rate (1000+ events/min).

4. **Clean Shutdown:** Ctrl+C gracefully stops capture and leaves no lingering ETW session.

5. **Privilege Handling:** Detects non-admin execution and provides clear error message.

6. **Output Quality:** JSONL output is valid, parseable, and follows documented schema.

7. **Documentation:** README includes installation, usage examples, and troubleshooting.

8. **Testing:** Basic unit tests pass. Windows CI runs successfully.

## 13. Open Questions and Decisions Needed

Please review and provide guidance on the following:

### Provider Selection
- **Q:** Should we support DNS-Server provider in addition to DNS-Client, or DNS-Client only for MVP?
- **Recommendation:** DNS-Client only for MVP, DNS-Server as future enhancement.

### Windows Version Support
- **Q:** What is the minimum Windows version you need to support? What is your primary target?
- **Recommendation:** Windows 10 (version 1809+) and Windows 11 as primary, Server 2019+ as secondary.

### Output Format
- **Q:** Is JSONL sufficient, or do you need CSV support in MVP?
- **Recommendation:** JSONL only for MVP, CSV as future enhancement.

### Anonymization
- **Q:** Should anonymization be opt-in (default off) or opt-out (default on)?
- **Recommendation:** Opt-in (default off) with clear documentation.

### Log Rotation
- **Q:** What are your preferred defaults for log rotation (size/time)?
- **Recommendation:** 100MB file size or 1 hour, whichever comes first. Keep last 10 files.

### Performance Targets
- **Q:** Are the proposed targets (5k events/min, <5% loss, <5% CPU, <200MB RAM) acceptable?
- **Recommendation:** Adjust based on your expected workload.

### Packaging
- **Q:** Pure Python script or bundled executable (PyInstaller/cx_Freeze)?
- **Recommendation:** Pure Python for MVP, executable as future enhancement.

### Latency Calculation
- **Q:** Is latency calculation (correlating start/stop events) required for MVP?
- **Recommendation:** Include if provider emits paired events, otherwise mark as future enhancement.

### Must-Have Fields
- **Q:** Which fields are must-have vs nice-to-have for acceptance?
- **Recommendation:** Must-have: timestamp, query_name, query_type, status. Nice-to-have: all others.

## 14. Appendix A: Provider Validation Tasks

To validate ETW provider availability and schema on a Windows machine, run:

```powershell
# List DNS-related providers
logman query providers | findstr /I DNS

# Get DNS-Client provider details
wevtutil gp Microsoft-Windows-DNS-Client /ge:true

# Get DNS-Server provider details (if available)
wevtutil gp Microsoft-Windows-DNS-Server /ge:true
```

Sample output should be captured and added to documentation for reference.

## 15. Timeline and Phases

### Phase 1: MVP (Current PRD)
- Core ETW subscription and event capture
- Basic filtering
- JSONL output
- CLI interface
- Documentation and basic tests

### Phase 2: Enhancements (Future)
- CSV output format
- DNS-Server provider support
- Advanced filtering and correlation
- Log rotation and management
- Performance optimizations

### Phase 3: Enterprise Features (Future)
- Offline ETL parsing
- Bundled executable
- Configuration management
- Integration examples
- Advanced analytics

---

## Approval

Please review this PRD and provide feedback on:
1. Overall scope and approach
2. Answers to open questions (Section 13)
3. Any missing requirements or use cases
4. Priority adjustments
5. Timeline expectations

Once approved, implementation can begin with a clear understanding of requirements and success criteria.
