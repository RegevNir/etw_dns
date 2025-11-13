"""
Command-line interface for ETW DNS capture tool.
"""

import argparse
import sys
import signal
from typing import Optional, Dict, Any

from .version import VERSION
from .privilege import check_privileges, is_windows
from .etw_provider import create_etw_provider
from .normalizer import EventNormalizer
from .filters import EventFilter
from .output import OutputWriter
from .stats import StatsTracker


class DNSCapture:
    """Main DNS capture application."""
    
    def __init__(self, args: argparse.Namespace):
        """
        Initialize DNS capture application.
        
        Args:
            args: Parsed command-line arguments.
        """
        self.args = args
        self.running = False
        
        self.normalizer = EventNormalizer()
        self.event_filter = EventFilter()
        self.output_writer = OutputWriter(
            output_file=args.out if args.out else None
        )
        self.stats_tracker = StatsTracker(
            report_interval=args.stats_interval
        )
        
        self._configure_filters()
        
        self.etw_provider = create_etw_provider(
            event_callback=self._on_event,
            use_fake=args.fake_provider
        )
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _configure_filters(self) -> None:
        """Configure event filters from command-line arguments."""
        if self.args.filter_domain:
            for pattern in self.args.filter_domain:
                self.event_filter.add_domain_filter(pattern)
        
        if self.args.filter_type:
            types = [t.strip() for t in self.args.filter_type.split(',')]
            self.event_filter.add_query_type_filter(types)
        
        if self.args.filter_status:
            statuses = [s.strip() for s in self.args.filter_status.split(',')]
            self.event_filter.add_status_filter(statuses)
        
        if self.args.include_process:
            processes = [p.strip() for p in self.args.include_process.split(',')]
            self.event_filter.add_process_filter(processes, exclude=False)
        
        if self.args.exclude_process:
            processes = [p.strip() for p in self.args.exclude_process.split(',')]
            self.event_filter.add_process_filter(processes, exclude=True)
    
    def _on_event(self, raw_event: Dict[str, Any]) -> None:
        """
        Callback for ETW events.
        
        Args:
            raw_event: Raw event from ETW provider.
        """
        try:
            self.stats_tracker.increment_captured()
            
            if self.args.debug_etw:
                print(f"[DEBUG] Raw event: {raw_event}", file=sys.stderr)
            
            event = self.normalizer.normalize(raw_event)
            if event is None:
                return
            
            if self.event_filter.has_filters():
                if not self.event_filter.should_include(event):
                    self.stats_tracker.increment_filtered()
                    return
            
            if self.output_writer.write_event(event):
                self.stats_tracker.increment_written()
            else:
                self.stats_tracker.increment_dropped()
            
        except Exception as e:
            self.stats_tracker.increment_errors()
            if self.args.log_level == "DEBUG":
                print(f"Error processing event: {e}", file=sys.stderr)
    
    def _signal_handler(self, signum, frame) -> None:
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        print("\nReceived shutdown signal, stopping capture...", file=sys.stderr)
        self.stop()
    
    def start(self) -> None:
        """Start DNS capture."""
        if self.running:
            return
        
        print("Starting ETW DNS capture...", file=sys.stderr)
        print(f"Output: {self.args.out if self.args.out else 'stdout'}", file=sys.stderr)
        
        if self.event_filter.has_filters():
            print("Filters enabled:", file=sys.stderr)
            if self.args.filter_domain:
                print(f"  Domain: {', '.join(self.args.filter_domain)}", file=sys.stderr)
            if self.args.filter_type:
                print(f"  Type: {self.args.filter_type}", file=sys.stderr)
            if self.args.filter_status:
                print(f"  Status: {self.args.filter_status}", file=sys.stderr)
            if self.args.include_process:
                print(f"  Include process: {self.args.include_process}", file=sys.stderr)
            if self.args.exclude_process:
                print(f"  Exclude process: {self.args.exclude_process}", file=sys.stderr)
        
        print("Press Ctrl+C to stop capture", file=sys.stderr)
        print("", file=sys.stderr)
        
        self.output_writer.start()
        self.stats_tracker.start()
        self.etw_provider.start()
        
        self.running = True
        
        try:
            while self.running and self.etw_provider.is_running():
                output_stats = self.output_writer.get_stats()
                self.stats_tracker.update_from_output_stats(output_stats)
                
                import time
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
    
    def stop(self) -> None:
        """Stop DNS capture."""
        if not self.running:
            return
        
        print("Stopping capture...", file=sys.stderr)
        
        self.running = False
        
        self.etw_provider.stop()
        self.stats_tracker.stop()
        self.output_writer.stop()
        
        print("Capture stopped.", file=sys.stderr)


def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.
    
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="etw_dns",
        description="ETW DNS Live Capture Tool - Capture DNS events on Windows via ETW",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m etw_dns
  
  python -m etw_dns --out dns.jsonl --filter-domain "*.example.com"
  
  python -m etw_dns --filter-type A,AAAA --include-process chrome.exe
  
  python -m etw_dns --debug-etw --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"etw_dns {VERSION}"
    )
    
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--out",
        metavar="PATH",
        help="Output file path (default: stdout)"
    )
    output_group.add_argument(
        "--format",
        choices=["jsonl"],
        default="jsonl",
        help="Output format (default: jsonl)"
    )
    
    filter_group = parser.add_argument_group("Filter Options")
    filter_group.add_argument(
        "--filter-domain",
        metavar="PATTERN",
        action="append",
        help="Filter by domain pattern (supports wildcards, e.g., *.example.com). Can be specified multiple times."
    )
    filter_group.add_argument(
        "--filter-type",
        metavar="TYPES",
        help="Filter by query type (comma-separated, e.g., A,AAAA,CNAME)"
    )
    filter_group.add_argument(
        "--filter-status",
        metavar="STATUSES",
        help="Filter by status (comma-separated, e.g., NOERROR,NXDOMAIN)"
    )
    filter_group.add_argument(
        "--include-process",
        metavar="NAMES",
        help="Include only these processes (comma-separated, e.g., chrome.exe,firefox.exe)"
    )
    filter_group.add_argument(
        "--exclude-process",
        metavar="NAMES",
        help="Exclude these processes (comma-separated)"
    )
    
    stats_group = parser.add_argument_group("Statistics Options")
    stats_group.add_argument(
        "--stats-interval",
        metavar="SECONDS",
        type=int,
        default=10,
        help="Statistics reporting interval in seconds (default: 10)"
    )
    
    debug_group = parser.add_argument_group("Debug Options")
    debug_group.add_argument(
        "--debug-etw",
        action="store_true",
        help="Print raw ETW events to stderr for debugging"
    )
    debug_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    debug_group.add_argument(
        "--fake-provider",
        action="store_true",
        help="Use fake ETW provider for testing (generates synthetic events)"
    )
    
    return parser


def main() -> int:
    """
    Main entry point for CLI.
    
    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.fake_provider:
        try:
            check_privileges()
        except SystemExit as e:
            return e.code
    
    try:
        capture = DNSCapture(args)
        capture.start()
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
