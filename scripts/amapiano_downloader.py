"""
amapiano_downloader.py — Batch downloader for the Amapiano MIR corpus.

Reads amapiano_tracks.csv and downloads each track via YouTube (yt-dlp).
Downloads are saved to amapiano_corpus/downloads/.
A download_log.csv tracks all results — re-runs skip already-successful tracks.

Usage:
    python amapiano_downloader.py                    # Download all HIGH confidence
    python amapiano_downloader.py --confidence ALL   # Include MEDIUM confidence
    python amapiano_downloader.py --limit 5          # Test run: first 5 tracks only
    python amapiano_downloader.py --limit 5 --confidence ALL
"""

import csv
import os
import sys
import time
import argparse
import datetime
from pathlib import Path
from music_dna.config import AMAPIANO_TRACKS_CSV, REPO_ROOT

# ── Paths ───────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
TRACKS_CSV   = AMAPIANO_TRACKS_CSV
DOWNLOAD_DIR = REPO_ROOT / "downloads" / "amapiano"
LOG_CSV      = REPO_ROOT / "data" / "legacy_benchmarks" / "amapiano_corpus" / "download_log.csv"

# ── Constants ───────────────────────────────────────────────────────────────────
SLEEP_BETWEEN_DL     = 2     # seconds between downloads (rate limiting)
LOG_FIELDNAMES = ["artist", "title", "genre_tag", "region", "status",
                  "source", "duration_s", "file_path", "timestamp"]


# ── Download Log ────────────────────────────────────────────────────────────────

def load_completed(log_path: Path) -> set:
    """Return set of (artist, title) already successfully downloaded."""
    completed = set()
    if not log_path.exists():
        return completed
    with open(log_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("status") == "success":
                completed.add((row["artist"].strip(), row["title"].strip()))
    return completed


def append_log(log_path: Path, row: dict):
    """Append one result row to the download log CSV."""
    write_header = not log_path.exists()
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


# ── Duration Check ──────────────────────────────────────────────────────────────

def get_duration(file_path: str) -> float:
    """Return duration in seconds using mutagen. Returns 0 on failure."""
    try:
        from mutagen.mp3 import MP3
        return MP3(file_path).info.length
    except Exception:
        return 0.0


# ── YouTube Download ────────────────────────────────────────────────────────────

def download_from_youtube(artist: str, title: str, output_dir: Path, min_duration: int) -> tuple:
    """
    Download a track from YouTube using yt-dlp.
    Returns (file_path, duration_seconds) on success, (None, 0) on failure.
    """
    import yt_dlp

    queries = [
        f"{artist} - {title} Official Audio",
        f"{artist} - {title} Official Video",
        f"{artist} {title} audio",
        f"{title} by {artist}",
    ]

    safe_name = f"{artist} - {title}".replace("/", "-").replace("\\", "-")
    output_template = str(output_dir / f"{safe_name}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1",
        "ignoreerrors": True,
        "no_playlist": True,
    }

    for query in queries:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if not info:
                    continue
                if "entries" in info:
                    if not info["entries"]:
                        continue
                    info = info["entries"][0]

                # Determine final filename
                expected = output_dir / f"{safe_name}.mp3"
                if expected.exists():
                    duration = get_duration(str(expected))
                    if duration >= min_duration:
                        return str(expected), duration
                    else:
                        print(f"    ⚠  Too short ({int(duration)}s) — likely wrong result, retrying...")
                        expected.unlink(missing_ok=True)
        except Exception:
            continue

    return None, 0.0


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Amapiano Corpus Downloader")
    parser.add_argument("--confidence", choices=["HIGH", "ALL"], default="HIGH",
                        help="Filter tracks by confidence: HIGH (default) or ALL")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max tracks to download (useful for test runs)")
    parser.add_argument("--output", type=Path, default=DOWNLOAD_DIR,
                        help="Output directory for MP3 files")
    parser.add_argument("--min-duration", type=int, default=180,
                        help="Minimum track duration in seconds (default: 180)")
    args = parser.parse_args()

    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load manifest
    if not TRACKS_CSV.exists():
        print(f"❌ Tracks CSV not found: {TRACKS_CSV}")
        sys.exit(1)

    with open(TRACKS_CSV, newline="", encoding="utf-8") as f:
        all_tracks = list(csv.DictReader(f))

    # Filter by confidence
    if args.confidence == "HIGH":
        tracks = [t for t in all_tracks if t.get("confidence") == "HIGH"]
    else:
        tracks = all_tracks

    # Apply limit
    if args.limit:
        tracks = tracks[:args.limit]

    # Skip already completed
    completed = load_completed(LOG_CSV)
    pending = [t for t in tracks if (t["artist"].strip(), t["title"].strip()) not in completed]
    skipped = len(tracks) - len(pending)

    print(f"\n🎵 Amapiano Corpus Downloader")
    print(f"   Manifest: {len(all_tracks)} total | {len(tracks)} after confidence filter")
    print(f"   Already downloaded: {skipped} | Pending: {len(pending)}")
    print(f"   Output: {output_dir.resolve()}\n")

    if not pending:
        print("✅ Nothing to download — all tracks already in log.")
        return

    success_count = 0
    fail_count = 0

    for i, track in enumerate(pending, 1):
        artist = track["artist"].strip()
        title  = track["title"].strip()
        genre  = track.get("genre_tag", "")
        region = track.get("region", "")

        print(f"[{i}/{len(pending)}] {artist} — {title}  ({genre}, {region})")

        file_path, duration = download_from_youtube(artist, title, output_dir, args.min_duration)

        status = "success" if file_path else "failed"
        if file_path:
            success_count += 1
            flag = ""
            # Flag core amapiano tracks that came back short (likely radio edit)
            if genre == "amapiano" and duration < 270:
                flag = " ⚠ SHORT — verify this is the full track"
            print(f"    ✅ {int(duration)}s → {Path(file_path).name}{flag}")
        else:
            fail_count += 1
            print(f"    ❌ Failed — no valid result found")

        append_log(LOG_CSV, {
            "artist":     artist,
            "title":      title,
            "genre_tag":  genre,
            "region":     region,
            "status":     status,
            "source":     "youtube",
            "duration_s": round(duration, 1) if duration else "",
            "file_path":  file_path or "",
            "timestamp":  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        time.sleep(SLEEP_BETWEEN_DL)

    print(f"\n{'='*50}")
    print(f"✅ Done: {success_count} downloaded, {fail_count} failed")
    print(f"📝 Log: {LOG_CSV.resolve()}")
    print(f"📁 Files: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
