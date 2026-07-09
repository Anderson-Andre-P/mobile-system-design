#!/usr/bin/env python3
"""Convenience entry point: identical to `python -m bookbuilder`."""
from bookbuilder.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
