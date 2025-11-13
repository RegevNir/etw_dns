"""
Event filtering logic for DNS events.
"""

from typing import List, Set
import fnmatch

from .schema import DNSEvent


class EventFilter:
    """Filters DNS events based on various criteria."""

    def __init__(self):
        """Initialize event filter with no filters."""
        self.domain_patterns: List[str] = []
        self.query_types: Set[str] = set()
        self.statuses: Set[str] = set()
        self.include_processes: Set[str] = set()
        self.exclude_processes: Set[str] = set()
        self.include_pids: Set[int] = set()
        self.exclude_pids: Set[int] = set()

    def add_domain_filter(self, pattern: str) -> None:
        """
        Add domain filter pattern.

        Args:
            pattern: Domain pattern (supports wildcards like *.example.com)
        """
        self.domain_patterns.append(pattern)

    def add_query_type_filter(self, query_types: List[str]) -> None:
        """
        Add query type filter.

        Args:
            query_types: List of query types to include (e.g., ["A", "AAAA"])
        """
        self.query_types.update(qt.upper() for qt in query_types)

    def add_status_filter(self, statuses: List[str]) -> None:
        """
        Add status filter.

        Args:
            statuses: List of statuses to include (e.g., ["NOERROR", "NXDOMAIN"])
        """
        self.statuses.update(s.upper() for s in statuses)

    def add_process_filter(self, processes: List[str], exclude: bool = False) -> None:
        """
        Add process name filter.

        Args:
            processes: List of process names to include/exclude.
            exclude: If True, exclude these processes; otherwise include.
        """
        if exclude:
            self.exclude_processes.update(p.lower() for p in processes)
        else:
            self.include_processes.update(p.lower() for p in processes)

    def add_pid_filter(self, pids: List[int], exclude: bool = False) -> None:
        """
        Add PID filter.

        Args:
            pids: List of PIDs to include/exclude.
            exclude: If True, exclude these PIDs; otherwise include.
        """
        if exclude:
            self.exclude_pids.update(pids)
        else:
            self.include_pids.update(pids)

    def should_include(self, event: DNSEvent) -> bool:
        """
        Check if event should be included based on filters.

        Args:
            event: DNS event to check.

        Returns:
            True if event passes all filters, False otherwise.
        """
        if self.domain_patterns and event.query_name:
            if not any(
                fnmatch.fnmatch(event.query_name.lower(), pattern.lower())
                for pattern in self.domain_patterns
            ):
                return False

        if self.query_types and event.query_type:
            if event.query_type.upper() not in self.query_types:
                return False

        if self.statuses and event.status:
            if event.status.upper() not in self.statuses:
                return False

        if self.exclude_processes and event.process_name:
            if event.process_name.lower() in self.exclude_processes:
                return False

        if self.include_processes and event.process_name:
            if event.process_name.lower() not in self.include_processes:
                return False

        if self.exclude_pids and event.pid is not None:
            if event.pid in self.exclude_pids:
                return False

        if self.include_pids and event.pid is not None:
            if event.pid not in self.include_pids:
                return False

        return True

    def has_filters(self) -> bool:
        """Check if any filters are configured."""
        return bool(
            self.domain_patterns
            or self.query_types
            or self.statuses
            or self.include_processes
            or self.exclude_processes
            or self.include_pids
            or self.exclude_pids
        )
