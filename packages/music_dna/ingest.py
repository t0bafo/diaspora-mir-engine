"""
ingest.py — Audio ingestion pipeline for Music DNA.

Scans directories of audio files, extracts features using the
diaspora-mir-engine's analyze_track module, and stores results
in the Music DNA database.

Supports two ingestion modes:
  1. Directory scan: artist/album/track folder structure
  2. Corpus import: existing JSON or CSV feature data
"""

import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

from .database import MusicDNADatabase

log = logging.getLogger(__name__)

# ── Import feature extractor from mir_engine ──────────────────────────────────
try:
    from mir_engine import extract_features as mir_extract_features
except ImportError:
    mir_extract_features = None
    log.warning(
        "mir_engine package not found. Audio analysis will not be available. "
        "Corpus import will still work."
    )

# ── Audio file extensions ─────────────────────────────────────────────────────
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".aiff", ".m4a"}


# ── Filename Parsing ──────────────────────────────────────────────────────────

def parse_filename(filename: str) -> tuple[Optional[str], str]:
    """
    Parse artist and title from a filename like:
      "Kelvin Momo ft. Babalwa M - Sukakude.mp3"
      → ("Kelvin Momo ft. Babalwa M", "Sukakude")

    Falls back to the full stem if no separator found.
    """
    stem = Path(filename).stem

    # Try common separators: " - ", " – ", " — "
    for sep in [" - ", " – ", " — "]:
        if sep in stem:
            parts = stem.split(sep, 1)
            artist = parts[0].strip()
            title = parts[1].strip()
            # Strip leading track numbers from title: "01 Track" → "Track"
            title = re.sub(r"^\d+[\.\)\-\s]+\s*", "", title)
            return artist, title

    # No separator found — try stripping track number from the whole stem
    title = re.sub(r"^\d+[\.\)\-\s]+\s*", "", stem)
    return None, title


def parse_primary_artist(artist_string: str) -> str:
    """
    Extract the primary artist from a string that may include features:
      "Kelvin Momo ft. Babalwa M" → "Kelvin Momo"
      "MDU aka TRP ft. Kabza De Small" → "MDU aka TRP"
    """
    for sep in [" ft.", " ft ", " feat.", " feat ", " Ft.", " Feat.", " x ", " X ", " & "]:
        if sep in artist_string:
            return artist_string.split(sep, 1)[0].strip()
    return artist_string.strip()


# ── Directory Ingestion ───────────────────────────────────────────────────────

def discover_audio_files(directory: Path) -> list[Path]:
    """Recursively find all audio files in a directory."""
    files = []
    for ext in AUDIO_EXTENSIONS:
        files.extend(directory.rglob(f"*{ext}"))
        files.extend(directory.rglob(f"*{ext.upper()}"))
    return sorted(set(files))


def infer_structure(file_path: Path, root: Path) -> tuple[Optional[str], Optional[str]]:
    """
    Infer artist and album from folder structure relative to root.

    Expected layouts:
      root/Artist/Album/track.mp3   → (Artist, Album)
      root/Artist/track.mp3         → (Artist, None)
      root/track.mp3                → (None, None)
    """
    try:
        rel = file_path.relative_to(root)
    except ValueError:
        return None, None

    parts = rel.parts[:-1]  # Exclude the filename itself

    if len(parts) >= 2:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], None
    else:
        return None, None


def _extract_features(file_path: Path) -> Optional[dict]:
    """Extract audio features using mir_engine. Returns None on failure."""
    if mir_extract_features is None:
        log.error("mir_engine module not available — cannot analyze audio files.")
        return None
    try:
        raw = mir_extract_features(file_path)
        return {
            "bpm": round(raw["bpm"], 2),
            "energy_rms": round(raw["energy"], 6),
            "onset_rate": round(raw["onsets"], 4),
            "rhythmic_complexity": raw["groove"]["rhythmic_complexity"],
            "syncopation": raw["groove"]["syncopation"],
            "pulse_clarity": raw["groove"]["pulse_clarity"],
            "log_drum_presence": raw["groove"]["log_drum_presence"],
            "danceability_custom": raw["groove"]["danceability_custom"],
            "duration": round(raw["duration"], 3),
            "backend": raw["backend"],
        }
    except Exception as e:
        log.error(f"Failed to analyze {file_path.name}: {e}")
        return None


def ingest_directory(
    directory: str,
    db: MusicDNADatabase,
    default_genre: Optional[str] = None,
) -> dict:
    """
    Scan a directory for audio files, extract features, and store in the database.

    Args:
        directory: Path to scan (expects artist/album/track structure).
        db: Database instance to store results.
        default_genre: Genre label to assign if not otherwise determinable.

    Returns:
        Summary dict with counts of processed/skipped/failed tracks.
    """
    root = Path(directory).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    files = discover_audio_files(root)
    if not files:
        log.warning(f"No audio files found in {root}")
        return {"processed": 0, "skipped": 0, "failed": 0}

    stats = {"processed": 0, "skipped": 0, "failed": 0}
    total = len(files)

    for i, fpath in enumerate(files, 1):
        file_str = str(fpath.resolve())

        # Skip already-ingested files
        if db.track_exists(file_str):
            log.info(f"[{i}/{total}] Skipping (already ingested): {fpath.name}")
            stats["skipped"] += 1
            continue

        log.info(f"[{i}/{total}] Analyzing: {fpath.name}")

        # Infer metadata from folder structure
        folder_artist, folder_album = infer_structure(fpath, root)

        # Also try parsing from filename
        filename_artist, track_title = parse_filename(fpath.name)

        # Determine artist (prefer folder structure, fall back to filename)
        artist_name = folder_artist or filename_artist
        if artist_name:
            primary_artist = parse_primary_artist(artist_name)
        else:
            primary_artist = "Unknown"

        # Try ID3 tags as a last resort
        try:
            import mutagen
            tags = mutagen.File(str(fpath), easy=True)
            if tags:
                if not artist_name and tags.get("artist"):
                    primary_artist = parse_primary_artist(tags["artist"][0])
                if not track_title and tags.get("title"):
                    track_title = tags["title"][0]
                if not folder_album and tags.get("album"):
                    folder_album = tags["album"][0]
        except Exception:
            pass

        # Extract audio features
        features = _extract_features(fpath)
        if features is None:
            stats["failed"] += 1
            continue

        # Store in database
        artist_id = db.add_artist(primary_artist)
        album_id = None
        if folder_album:
            album_id = db.add_album(folder_album, artist_id)

        db.add_track(
            title=track_title,
            features=features,
            artist_id=artist_id,
            album_id=album_id,
            file_path=file_str,
            genre=default_genre,
            duration=features.get("duration"),
            backend=features.get("backend"),
        )
        stats["processed"] += 1

        # Progress update every 10 tracks
        if stats["processed"] % 10 == 0:
            log.info(
                f"  Progress: {stats['processed']} analyzed, "
                f"{stats['skipped']} skipped, {stats['failed']} failed"
            )

    return stats


# ── Corpus Import ─────────────────────────────────────────────────────────────

def import_corpus_json(json_path: str, db: MusicDNADatabase) -> dict:
    """
    Import the existing diaspora_corpus_features JSON into the database.

    Expected format: { "all_tracks": [ {artist, title, genre, bpm, ...}, ... ] }
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Corpus file not found: {path}")

    with open(path) as f:
        corpus = json.load(f)

    tracks = corpus.get("all_tracks", [])
    if not tracks and corpus.get("hero_tracks"):
        tracks = corpus["hero_tracks"]

    stats = {"imported": 0, "skipped": 0}
    total = len(tracks)

    for i, t in enumerate(tracks, 1):
        artist_name = t.get("artist", "Unknown")
        title = t.get("title", f"Track {i}")
        primary_artist = parse_primary_artist(artist_name)

        artist_id = db.add_artist(primary_artist)

        # Check for duplicates
        if db.track_exists_by_title_artist(title, artist_id):
            stats["skipped"] += 1
            continue

        features = {
            "bpm": t.get("bpm"),
            "energy_rms": t.get("energy_rms", t.get("energy")),
            "onset_rate": t.get("onset_rate"),
            "rhythmic_complexity": t.get("complexity", t.get("rhythmic_complexity")),
            "syncopation": t.get("syncopation"),
            "pulse_clarity": t.get("pulse_clarity"),
            "log_drum_presence": t.get("log_drum", t.get("log_drum_presence")),
            "danceability_custom": t.get("danceability", t.get("danceability_custom")),
        }

        db.add_track(
            title=title,
            features=features,
            artist_id=artist_id,
            genre=t.get("genre"),
        )
        stats["imported"] += 1

        if stats["imported"] % 50 == 0:
            log.info(f"  Imported {stats['imported']}/{total} tracks...")

    log.info(f"Corpus import complete: {stats['imported']} imported, {stats['skipped']} skipped.")
    return stats


def import_corpus_csv(csv_path: str, db: MusicDNADatabase) -> dict:
    """
    Import a CSV dataset (e.g., merged_dataset_v1.csv) into the database.

    Expected columns: file_name, genre, bpm, energy, onset_rate, complexity,
                      syncopation, pulse_clarity, log_drum, danceability, backend
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    stats = {"imported": 0, "skipped": 0}

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)

    for i, row in enumerate(rows, 1):
        filename = row.get("file_name", f"track_{i}")

        # Parse artist and title from filename
        artist_name, title = parse_filename(filename)
        if not artist_name:
            artist_name = "Unknown"
        primary_artist = parse_primary_artist(artist_name)

        artist_id = db.add_artist(primary_artist)

        if db.track_exists_by_title_artist(title, artist_id):
            stats["skipped"] += 1
            continue

        def safe_float(val):
            try:
                return float(val) if val else None
            except (ValueError, TypeError):
                return None

        features = {
            "bpm": safe_float(row.get("bpm")),
            "energy_rms": safe_float(row.get("energy")),
            "onset_rate": safe_float(row.get("onset_rate")),
            "rhythmic_complexity": safe_float(row.get("complexity")),
            "syncopation": safe_float(row.get("syncopation")),
            "pulse_clarity": safe_float(row.get("pulse_clarity")),
            "log_drum_presence": safe_float(row.get("log_drum")),
            "danceability_custom": safe_float(row.get("danceability")),
        }

        db.add_track(
            title=title,
            features=features,
            artist_id=artist_id,
            genre=row.get("genre"),
            backend=row.get("backend"),
        )
        stats["imported"] += 1

    log.info(f"CSV import complete: {stats['imported']} imported, {stats['skipped']} skipped.")
    return stats
