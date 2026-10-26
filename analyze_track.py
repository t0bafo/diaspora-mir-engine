"""
analyze_track.py — Backward-compatibility shim during layout refactoring.
Re-exports from packages.mir_engine.extractor.
"""
import sys
from pathlib import Path

_PACKAGES_DIR = str(Path(__file__).resolve().parent / "packages")
if _PACKAGES_DIR not in sys.path:
    sys.path.insert(0, _PACKAGES_DIR)

from mir_engine.extractor import *
from mir_engine.extractor import main

if __name__ == "__main__":
    main()
