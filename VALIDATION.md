# Windows Validation Guide

This guide provides steps for manually validating the ETW DNS capture tool on Windows systems.

## Prerequisites

- Windows 10/11 or Windows Server 2019+
- Python 3.10 or higher
- Administrative privileges
- Internet connectivity for DNS queries

## Installation

1. Clone the repository:
```powershell
git clone https://github.com/RegevNir/etw_dns.git
cd etw_dns
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

## Provider Validation

Before running the tool, verify that the Microsoft-Windows-DNS-Client provider is available on your system.

### List DNS-related ETW Providers

```powershell
logman query providers | findstr /I DNS
```

Expected output should include:
```
Microsoft-Windows-DNS-Client          {1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}
```

### Get Provider Details

```powershell
wevtutil gp Microsoft-Windows-DNS-Client /ge:true
```

This command displays the provider manifest, including:
- Provider GUID
- Available event IDs
- Event field names and types

**Save this output** to `docs/provider_manifest.txt` for reference.

### Sample Provider Output

```
name: Microsoft-Windows-DNS-Client
guid: {1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}
helpLink: https://go.microsoft.com/fwlink/events.asp?CoName=Microsoft%20Corporation&ProdName=Microsoft%c2%ae%20Windows%c2%ae%20Operating%20System&ProdVer=10.0.19041.1&FileName=DnsClientPSProvider.dll&FileVer=10.0.19041.1
resourceFileName: C:\Windows\System32\DnsClientPSProvider.dll
messageFileName: C:\Windows\System32\DnsClientPSProvider.dll
...
```

## Basic Validation Tests

### Test 1: Privilege Detection

Run the tool without administrator privileges:

```powershell
python -m etw_dns
```

**Expected result:** Error message indicating administrative privileges are required, with exit code 2.

### Test 2: Basic Capture

Run the tool with administrator privileges:

```powershell
# Open PowerShell as Administrator
python -m etw_dns
```

In another window, generate DNS traffic:
```powershell
nslookup google.com
nslookup github.com
nslookup microsoft.com
```

**Expected result:** 
- Tool starts successfully
- DNS events appear in stdout as JSONL
- Statistics are printed to stderr every 10 seconds
- Ctrl+C stops capture cleanly

### Test 3: File Output

Capture to a file:

```powershell
python -m etw_dns --out test_capture.jsonl
```

Generate DNS traffic, then stop capture with Ctrl+C.

Verify the output file:
```powershell
Get-Content test_capture.jsonl | Select-Object -First 5
```

**Expected result:**
- File contains valid JSONL (one JSON object per line)
- Each event has required fields: `schema_version`, `tool_version`, `timestamp`
- Events contain DNS-specific fields: `query_name`, `query_type`, `status`

### Test 4: Domain Filtering

Capture only Google domains:

```powershell
python -m etw_dns --filter-domain "*.google.com" --out google_only.jsonl
```

Generate mixed DNS traffic:
```powershell
nslookup www.google.com
nslookup github.com
nslookup mail.google.com
nslookup microsoft.com
```

Stop capture and verify:
```powershell
Get-Content google_only.jsonl | ConvertFrom-Json | Select-Object query_name
```

**Expected result:** Only queries for `*.google.com` domains are captured.

### Test 5: Query Type Filtering

Capture only A and AAAA records:

```powershell
python -m etw_dns --filter-type A,AAAA --out type_filter.jsonl
```

Generate DNS traffic and verify output contains only A and AAAA queries.

### Test 6: Process Filtering

Capture only from specific browser:

```powershell
python -m etw_dns --include-process chrome.exe --out chrome_only.jsonl
```

Open Chrome and browse to several websites. Verify output contains only events from chrome.exe.

### Test 7: Debug Mode

Run with debug output:

```powershell
python -m etw_dns --debug-etw --log-level DEBUG
```

**Expected result:** Raw ETW events are printed to stderr, showing the actual event structure from the provider.

### Test 8: Statistics

Run capture for 60 seconds and observe statistics:

```powershell
python -m etw_dns --stats-interval 10
```

Generate continuous DNS traffic (browse websites, run continuous nslookup, etc.).

**Expected result:**
- Statistics printed every 10 seconds
- Counters increase appropriately
- Final statistics printed on exit
- Drop rate should be <5% under normal load

### Test 9: Graceful Shutdown

Start capture:
```powershell
python -m etw_dns --out shutdown_test.jsonl
```

Generate some DNS traffic, then press Ctrl+C.

**Expected result:**
- Tool responds immediately to Ctrl+C
- "Stopping capture..." message appears
- Final statistics are printed
- File is properly closed
- No lingering ETW sessions (verify with `logman query -ets`)

### Test 10: Long-Running Stability

Run capture for extended period (e.g., 1 hour):

```powershell
python -m etw_dns --out long_run.jsonl --stats-interval 60
```

Let it run while performing normal computer activities.

**Expected result:**
- No crashes or errors
- Memory usage remains stable (<200MB)
- CPU usage remains low (<5%)
- Events continue to be captured throughout
- Clean shutdown when stopped

## Performance Validation

### High Load Test

Generate high DNS query rate:

```powershell
# In PowerShell, run multiple parallel nslookup queries
1..100 | ForEach-Object -Parallel {
    nslookup "test$_.example.com"
} -ThrottleLimit 10
```

While running the capture tool, monitor:
- Event drop rate (should be <5%)
- CPU usage (should be <5%)
- Memory usage (should be <200MB)

## Field Validation

Examine captured events to verify field presence and accuracy:

```powershell
# Parse and display events
Get-Content test_capture.jsonl | ForEach-Object {
    $event = $_ | ConvertFrom-Json
    Write-Host "Query: $($event.query_name) Type: $($event.query_type) Status: $($event.status) PID: $($event.pid) Process: $($event.process_name)"
}
```

Verify:
- `timestamp` is in ISO 8601 format
- `query_name` matches actual DNS queries
- `query_type` is correct (A, AAAA, etc.)
- `status` reflects query results (NOERROR, NXDOMAIN, etc.)
- `pid` and `process_name` are present and accurate
- `hostname` matches local machine name

## Known Limitations

### DoH/DoT Queries

DNS over HTTPS (DoH) queries may not appear in the capture:

Test:
```powershell
# Enable DoH in browser settings
# Browse websites
# Check if queries appear in capture
```

**Expected:** DoH queries may not be visible, as they bypass traditional DNS client APIs.

### System Process Queries

Some system processes may not expose full process information:

```powershell
# Look for events with missing process_name
Get-Content test_capture.jsonl | ConvertFrom-Json | Where-Object { -not $_.process_name }
```

This is expected behavior for certain system-level queries.

## Troubleshooting

### No Events Captured

1. Verify provider is available:
```powershell
logman query providers | findstr /I "DNS-Client"
```

2. Check for active ETW sessions:
```powershell
logman query -ets
```

3. Verify DNS traffic is occurring:
```powershell
nslookup google.com
```

4. Run with debug mode:
```powershell
python -m etw_dns --debug-etw
```

### High Drop Rate

If events are being dropped:

1. Reduce filter complexity
2. Write to faster storage (SSD)
3. Increase system resources
4. Check for disk I/O bottlenecks

### Permission Errors

Ensure you're running from an elevated prompt:
```powershell
# Check if running as admin
([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
```

Should return `True`.

## Validation Checklist

- [ ] Provider is available on system
- [ ] Privilege detection works correctly
- [ ] Basic capture works
- [ ] File output works
- [ ] Domain filtering works
- [ ] Query type filtering works
- [ ] Process filtering works
- [ ] Debug mode shows raw events
- [ ] Statistics are accurate
- [ ] Graceful shutdown works
- [ ] No lingering ETW sessions after exit
- [ ] Long-running stability (1+ hour)
- [ ] Performance meets targets (<5% CPU, <200MB RAM, <5% drops)
- [ ] Field accuracy verified
- [ ] JSONL output is valid

## Reporting Issues

When reporting issues, please include:

1. Windows version: `winver`
2. Python version: `python --version`
3. Provider manifest: `wevtutil gp Microsoft-Windows-DNS-Client /ge:true`
4. Tool output with `--debug-etw --log-level DEBUG`
5. Sample events from output file
6. Statistics from final report
7. Steps to reproduce

## Windows Version Matrix

Test on multiple Windows versions if possible:

| Version | Tested | Notes |
|---------|--------|-------|
| Windows 10 21H2 | | |
| Windows 10 22H2 | | |
| Windows 11 21H2 | | |
| Windows 11 22H2 | | |
| Windows Server 2019 | | |
| Windows Server 2022 | | |

Document any version-specific behaviors or issues.
