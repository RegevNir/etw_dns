# ETW DNS Live Capture Tool

A Windows-only Python CLI tool that subscribes to ETW (Event Tracing for Windows) DNS providers to capture live DNS resolution activity in real time and emit structured records in JSONL format.

## Features

- **Real-time DNS capture** via ETW Microsoft-Windows-DNS-Client provider
- **JSONL output** with structured, versioned schema
- **Flexible filtering** by domain, query type, status, process, and PID
- **Process enrichment** with PID, process name, and activity correlation
- **Statistics tracking** with periodic reporting
- **Graceful shutdown** with proper ETW session cleanup
- **Non-blocking architecture** with queued event processing
- **Privilege detection** with helpful error messages

## Requirements

- **Windows 10/11** or **Windows Server 2019+**
- **Python 3.10+**
- **Administrative privileges** (required for ETW access)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RegevNir/etw_dns.git
cd etw_dns
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

The tool uses `pywintrace` from GitHub (v0.3.0) for ETW access.

## Usage

### Basic Usage

Capture DNS events to stdout:
```bash
python -m etw_dns
```

**Note:** You must run from an elevated command prompt or PowerShell (Run as Administrator).

### Output to File

Capture to a JSONL file:
```bash
python -m etw_dns --out dns_events.jsonl
```

### Filtering

Filter by domain pattern (supports wildcards):
```bash
python -m etw_dns --filter-domain "*.example.com" --filter-domain "*.google.com"
```

Filter by query type:
```bash
python -m etw_dns --filter-type A,AAAA
```

Filter by status:
```bash
python -m etw_dns --filter-status NOERROR,NXDOMAIN
```

Filter by process:
```bash
# Include only specific processes
python -m etw_dns --include-process chrome.exe,firefox.exe

# Exclude specific processes
python -m etw_dns --exclude-process svchost.exe
```

### Combined Example

Capture Chrome and Firefox DNS queries for specific domains:
```bash
python -m etw_dns \
  --out browser_dns.jsonl \
  --filter-domain "*.google.com" \
  --filter-type A,AAAA \
  --include-process chrome.exe,firefox.exe \
  --stats-interval 30
```

### Debug Mode

View raw ETW events for troubleshooting:
```bash
python -m etw_dns --debug-etw --log-level DEBUG
```

### Testing Without Windows

Use the fake provider for development and testing on non-Windows platforms:
```bash
python -m etw_dns --fake-provider
```

This generates synthetic DNS events for testing the tool's functionality.

## Command-Line Options

### Output Options
- `--out PATH` - Output file path (default: stdout)
- `--format {jsonl}` - Output format (currently only JSONL supported)

### Filter Options
- `--filter-domain PATTERN` - Filter by domain pattern (can be specified multiple times)
- `--filter-type TYPES` - Filter by query type (comma-separated: A,AAAA,CNAME,etc.)
- `--filter-status STATUSES` - Filter by status (comma-separated: NOERROR,NXDOMAIN,etc.)
- `--include-process NAMES` - Include only these processes (comma-separated)
- `--exclude-process NAMES` - Exclude these processes (comma-separated)

### Statistics Options
- `--stats-interval SECONDS` - Statistics reporting interval (default: 10)

### Debug Options
- `--debug-etw` - Print raw ETW events to stderr
- `--log-level {DEBUG,INFO,WARNING,ERROR}` - Log level (default: INFO)
- `--fake-provider` - Use fake provider for testing

## Output Format

Events are output in JSONL (JSON Lines) format, with one JSON object per line. See [SCHEMA.md](SCHEMA.md) for detailed schema documentation.

Example event:
```json
{
  "schema_version": "1.0",
  "tool_version": "0.1.0",
  "timestamp": "2025-11-13T12:00:00.123Z",
  "query_name": "example.com",
  "query_type": "A",
  "status": "NOERROR",
  "server_ip": "8.8.8.8",
  "pid": 1234,
  "process_name": "chrome.exe",
  "hostname": "WORKSTATION01",
  "provider_name": "Microsoft-Windows-DNS-Client",
  "provider_guid": "{1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}"
}
```

## Statistics

The tool reports statistics to stderr at regular intervals (default: every 10 seconds):

```
[Stats] Captured: 1523, Filtered: 234, Written: 1289, Dropped: 0, Errors: 0, Rate: 12.5 events/sec
```

Final statistics are printed when the tool exits.

## Graceful Shutdown

Press `Ctrl+C` to stop capture. The tool will:
1. Stop the ETW session cleanly
2. Flush all buffered events
3. Print final statistics
4. Exit with code 0

## Troubleshooting

### "Administrative privileges required"

The tool requires administrator rights to access ETW. Run from an elevated command prompt:
1. Right-click Command Prompt or PowerShell
2. Select "Run as administrator"
3. Run the tool again

### "This tool requires Windows to run"

ETW is Windows-only. For testing on other platforms, use `--fake-provider`.

### No events captured

- Verify DNS activity is occurring (browse websites, run `nslookup`, etc.)
- Check that filters aren't too restrictive
- Use `--debug-etw` to see raw ETW events
- Ensure the Microsoft-Windows-DNS-Client provider is available

### High event drop rate

If you see many dropped events:
- Reduce filter complexity
- Write to a faster disk
- Increase system resources
- Check for disk I/O bottlenecks

## Architecture

The tool uses a modular architecture:

- `etw_provider.py` - ETW provider interface (Real + Fake implementations)
- `normalizer.py` - Converts raw ETW events to structured schema
- `filters.py` - Event filtering logic
- `output.py` - Non-blocking JSONL writer with queue
- `stats.py` - Statistics tracking and reporting
- `privilege.py` - Windows privilege detection
- `cli.py` - Command-line interface
- `schema.py` - Event schema definitions

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Testing Locally

Use the fake provider for local testing without Windows:
```bash
python -m etw_dns --fake-provider --out test.jsonl
```

### Windows Validation

See [VALIDATION.md](VALIDATION.md) for manual validation steps on Windows.

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or pull request.

## Acknowledgments

- Uses [pywintrace](https://github.com/fireeye/pywintrace) by FireEye for ETW access
- Built according to the PRD in [PRD.md](PRD.md)

## Support

For issues and questions, please open a GitHub issue.
