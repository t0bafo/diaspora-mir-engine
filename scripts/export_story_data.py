"""
scripts/export_story_data.py — Export story_data.json for music-dna-story.

Generates data/exports/story_data.json matching the Remotion app schema:
  - version, total_tracks, genres
  - hero_tracks (15 key tracks with full acoustic features)
  - all_tracks (294 tracks with normalized groove metrics)
"""

import json
import logging
from pathlib import Path
from mir_engine.config import CORPUS_PATH, EXPORT_DIR, REPO_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("export_story_data")


def export_story_data(output_path: Path = None) -> Path:
    target_path = output_path or (EXPORT_DIR / "story_data.json")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Source data from apps/music-dna-story/src/data.json or corpus
    src_path = REPO_ROOT / "apps" / "music-dna-story" / "src" / "data.json"
    if not src_path.exists():
        src_path = CORPUS_PATH

    with open(src_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Write serialized json matching Remotion schema
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    log.info(f"Exported story data to: {target_path}")
    return target_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export story_data.json for Remotion story app")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output file path")
    args = parser.parse_args()

    export_story_data(args.output)
