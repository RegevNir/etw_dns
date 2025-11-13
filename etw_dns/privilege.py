"""
Privilege detection for Windows administrative rights.
"""

import sys
import platform


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def is_admin() -> bool:
    """
    Check if the current process has administrative privileges.

    Returns:
        bool: True if running with admin privileges, False otherwise.
    """
    if not is_windows():
        return False

    try:
        import ctypes

        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def check_privileges() -> None:
    """
    Check if running with required privileges and exit if not.

    Raises:
        SystemExit: If not running on Windows or without admin privileges.
    """
    if not is_windows():
        print("Error: This tool requires Windows to run.", file=sys.stderr)
        print(
            "ETW (Event Tracing for Windows) is only available on Windows.",
            file=sys.stderr,
        )
        sys.exit(5)

    if not is_admin():
        print("Error: Administrative privileges required.", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "This tool requires administrator rights to subscribe to ETW events.",
            file=sys.stderr,
        )
        print(
            "Please run this tool from an elevated command prompt or PowerShell.",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        print("To elevate:", file=sys.stderr)
        print("  1. Right-click Command Prompt or PowerShell", file=sys.stderr)
        print("  2. Select 'Run as administrator'", file=sys.stderr)
        print("  3. Run the tool again", file=sys.stderr)
        sys.exit(2)
