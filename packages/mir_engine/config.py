"""
config.py — Centralized path configuration for the MIR engine and scripts.
Resolves defaults relative to the repository root (located by finding pyproject.toml upward).
All paths can be overridden via environment variables.
"""

import os
from pathlib import Path


def find_repo_root(start_path: Path = None) -> Path:
    """Find the root of the repository by walking upward until pyproject.toml is found."""
    current = (start_path or Path(__file__)).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return Path(__file__).resolve().parent.parent.parent


REPO_ROOT = find_repo_root()

# Canonical Corpus Path
CORPUS_PATH = Path(
    os.getenv(
        "MIR_CORPUS_PATH",
        str(REPO_ROOT / "data" / "corpus" / "diaspora_corpus_features_v1_3.json"),
    )
).resolve()

# Export Directory
EXPORT_DIR = Path(
    os.getenv("MIR_EXPORT_DIR", str(REPO_ROOT / "data" / "exports"))
).resolve()

# Legacy Benchmark / Dataset Paths
AMAPIANO_TRACKS_CSV = Path(
    os.getenv(
        "MIR_AMAPIANO_TRACKS_CSV",
        str(REPO_ROOT / "data" / "corpus" / "amapiano_tracks.csv"),
    )
).resolve()

BENCHMARKS_DIR = REPO_ROOT / "data" / "legacy_benchmarks"
