"""
Main entry point for running etw_dns as a module.

Usage:
    python -m etw_dns [options]
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
