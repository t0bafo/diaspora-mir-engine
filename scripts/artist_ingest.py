"""
scripts/artist_ingest.py — Download an artist's audio folder from Google Drive.

Files land in <MIR_ARTIST_DATA_DIR>/<artist>/audio/. Point MIR_ARTIST_DATA_DIR at
private storage: artist audio must never be committed (the repo is public).

Usage:
    MIR_ARTIST_DATA_DIR=/path/to/private/store \
        python scripts/artist_ingest.py sikiboi https://drive.google.com/drive/folders/<id>
"""

import argparse
import logging
from pathlib import Path

from mir_engine.config import ARTIST_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("artist_ingest")

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aiff", ".aif", ".ogg"}


def ingest(artist: str, folder_url: str) -> Path:
    import gdown

    audio_dir = ARTIST_DATA_DIR / artist / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    listing = gdown.download_folder(folder_url, skip_download=True, quiet=True)
    log.info(f"{len(listing)} files in Drive folder")

    downloaded, skipped = 0, 0
    for item in listing:
        name = Path(item.path).name
        if Path(name).suffix.lower() not in AUDIO_EXTENSIONS:
            log.info(f"Skipping non-audio file: {name}")
            continue
        target = audio_dir / name
        if target.exists() and target.stat().st_size > 0:
            skipped += 1
            continue
        gdown.download(id=item.id, output=str(target), quiet=True)
        downloaded += 1
        log.info(f"Downloaded {name} ({target.stat().st_size / 1e6:.1f} MB)")

    log.info(f"Done: {downloaded} downloaded, {skipped} already present → {audio_dir}")
    return audio_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download an artist's Drive folder")
    parser.add_argument("artist", help="Artist slug, e.g. sikiboi")
    parser.add_argument("folder_url", help="Google Drive folder URL (shared with link)")
    args = parser.parse_args()
    ingest(args.artist, args.folder_url)
