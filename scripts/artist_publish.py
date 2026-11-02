"""
scripts/artist_publish.py — Copy an artist's results (not audio) to the private data repo the dashboard reads.

Uploads tracks.csv and profile.json from <MIR_ARTIST_DATA_DIR>/<artist>/ to the private GitHub repo.
listening_notes.csv is only uploaded if the repo doesn't have one yet, so notes saved from the dashboard
are never overwritten.

Usage:
    MIR_ARTIST_DATA_DIR=/path/to/private/store \\
    MIR_ARTIST_GITHUB_REPO=t0bafo/artist-data MIR_ARTIST_GITHUB_TOKEN=... \\
    python scripts/artist_publish.py sikiboi
"""

import argparse
import logging
import os

from mir_engine.artist_store import GitHubArtistStore, LocalArtistStore
from mir_engine.config import ARTIST_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("artist_publish")


def publish(artist: str, local: LocalArtistStore, remote: GitHubArtistStore) -> None:
    for name in ("tracks.csv", "profile.json"):
        text = local.read_text(artist, name)
        if text is None:
            raise SystemExit(f"Missing {name} for {artist} in {local.label}; run scripts/artist_profile.py first")
        remote.write_text(artist, name, text, message=f"{artist}: update {name}")
        log.info(f"Uploaded {artist}/{name}")

    notes = local.read_text(artist, "listening_notes.csv")
    if notes is not None and remote.read_text(artist, "listening_notes.csv") is None:
        remote.write_text(artist, "listening_notes.csv", notes, message=f"{artist}: add listening notes template")
        log.info(f"Uploaded {artist}/listening_notes.csv")
    else:
        log.info("Kept the listening notes already in the repo")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish an artist's results to the private data repo")
    parser.add_argument("artist", help="Artist slug, e.g. sikiboi")
    args = parser.parse_args()

    repo, token = os.getenv("MIR_ARTIST_GITHUB_REPO"), os.getenv("MIR_ARTIST_GITHUB_TOKEN")
    if not (repo and token):
        raise SystemExit("Set MIR_ARTIST_GITHUB_REPO and MIR_ARTIST_GITHUB_TOKEN")
    remote = GitHubArtistStore(repo, token, branch=os.getenv("MIR_ARTIST_GITHUB_BRANCH") or "main")
    publish(args.artist, LocalArtistStore(ARTIST_DATA_DIR), remote)
