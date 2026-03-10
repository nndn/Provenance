#!/usr/bin/env python3
"""
Provenance CLI — spec-driven development. Python 3.9+ stdlib only.
Run: python prov/prov.py <command> [args]
"""
import sys

from prov import main

if __name__ == "__main__":
    sys.exit(main())
