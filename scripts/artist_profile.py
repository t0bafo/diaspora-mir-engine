"""
scripts/artist_profile.py — Compute an artist's sonic profile against the corpus.

Reads <MIR_ARTIST_DATA_DIR>/<artist>/audio/, analyzes every track with mir_engine,
and writes to <MIR_ARTIST_DATA_DIR>/<artist>/:
  - tracks.csv              one row per file: features, key, loudness, genre lean, sounds-like
  - profile.json            artist-level signature, lane, cohesion, standouts
  - listening_notes.csv     template for the analyst's ear-vs-numbers check (never overwritten)

See docs/artist-profile/SPEC.md.

Usage:
    MIR_ARTIST_DATA_DIR=/path/to/private/store python scripts/artist_profile.py sikiboi
"""

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from mir_engine import extract_features
from mir_engine.config import ARTIST_DATA_DIR, CORPUS_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("artist_profile")

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aiff", ".aif", ".ogg"}

# Track column -> corpus column, for the 6 features both share
SHARED_FEATURES = {
    "bpm": "bpm",
    "syncopation": "syncopation",
    "pulse_clarity": "pulse_clarity",
    "rhythmic_complexity": "complexity",
    "log_drum_presence": "log_drum",
    "groove_score": "danceability",
}
GENRES = ["afrobeats", "amapiano", "afropiano"]
K_NEIGHBOURS = 15

VERSION_PATTERNS = [
    ("demo", r"\bdemo\b"),
    ("unmixed", r"\bunmixed\b"),
    ("master", r"\b(mstr|master|mastered)\b"),
    ("slowed", r"\b(slow down|slowed)\b"),
    ("original", r"\boriginal\b"),
    ("main", r"\bmain\b"),
]
ARTIST_TOKENS = r"\b(siki ?boi|siki)\b"
COLLAB_PATTERN = r"(\bft\.?\b|\bfeat\.?\b|\bx\b|&|\bdj\b)"
DATE_PATTERN = r"^\s*\d{1,2}[:/.-]\d{1,2}[:/.-]\d{2,4}"


def parse_name(file_name: str) -> dict:
    """Derive a readable title, version tag, collab flag and song-group key from a file name."""
    stem = Path(file_name).stem.replace("_", " ")
    stem = re.sub(r"\[([^\]]*)\]", r" \1 ", stem)
    lower = stem.lower()

    version = next((tag for tag, pat in VERSION_PATTERNS if re.search(pat, lower)), "")
    collab = bool(re.search(COLLAB_PATTERN, lower))

    title = stem
    if " - " in stem:
        left, right = stem.split(" - ", 1)
        title = left if re.match(DATE_PATTERN, right) else right
        if not re.search(ARTIST_TOKENS, left, re.I) and re.search(ARTIST_TOKENS, right, re.I):
            collab = True
    title = re.sub(ARTIST_TOKENS, " ", title, flags=re.I)
    for _, pat in VERSION_PATTERNS:
        title = re.sub(pat, " ", title, flags=re.I)
    title = re.sub(r"[^\w' ]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip().title() or stem.strip()

    words = [w for w in title.lower().split() if len(w) > 2] or title.lower().split()
    return {"title": title, "version": version, "collab": collab, "song_group": words[0] if words else title.lower()}


def key_loudness_duration(path: Path) -> dict:
    import essentia.standard as es

    audio, sr, channels, *_ = es.AudioLoader(filename=str(path))()
    out = {"duration_s": round(len(audio) / sr, 1), "key": None, "loudness_lufs": None}
    try:
        _, _, integrated, _ = es.LoudnessEBUR128(sampleRate=sr)(audio)
        out["loudness_lufs"] = round(float(integrated), 1)
    except Exception as e:
        log.warning(f"Loudness failed for {path.name}: {e}")
    try:
        mono = es.MonoMixer()(audio, channels)
        if sr != 44100:
            mono = es.Resample(inputSampleRate=sr, outputSampleRate=44100)(mono)
        key, scale, strength = es.KeyExtractor(profileType="edma")(mono)
        out["key"] = f"{key} {scale}"
        out["key_strength"] = round(float(strength), 3)
    except Exception as e:
        log.warning(f"Key detection failed for {path.name}: {e}")
    return out


def analyze_file(path: Path) -> dict:
    res = extract_features(path)
    g = res["groove"]
    row = {
        "file_name": path.name,
        **parse_name(path.name),
        "bpm": round(float(res["bpm"]), 2),
        "energy_rms": round(float(res["energy"]), 6),
        "onset_rate": round(float(res["onsets"]), 4),
        "rhythmic_complexity": g["rhythmic_complexity"],
        "syncopation": g["syncopation"],
        "pulse_clarity": g["pulse_clarity"],
        "log_drum_presence": g["log_drum_presence"],
        "groove_score": g["danceability_custom"],
        "backend": res["backend"],
    }
    row.update(key_loudness_duration(path))
    return row


def load_corpus() -> pd.DataFrame:
    data = json.loads(CORPUS_PATH.read_text())
    df = pd.DataFrame(data["all_tracks"])
    return df.dropna(subset=list(SHARED_FEATURES.values()))


def knn_genre_lean(tracks: pd.DataFrame, corpus: pd.DataFrame, features: dict) -> pd.Series:
    corpus_cols, track_cols = list(features.values()), list(features.keys())
    mean = corpus[corpus_cols].mean().values
    std = corpus[corpus_cols].std().replace(0, 1).values
    cz = (corpus[corpus_cols].values - mean) / std
    tz = (tracks[track_cols].astype(float).values - mean) / std
    leans = []
    for vec in tz:
        nearest = corpus.iloc[np.argsort(np.linalg.norm(cz - vec, axis=1))[:K_NEIGHBOURS]]
        leans.append(nearest["genre"].value_counts().idxmax())
    return pd.Series(leans, index=tracks.index)


def compare_to_corpus(tracks: pd.DataFrame, corpus: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    corpus_cols = list(SHARED_FEATURES.values())
    track_cols = list(SHARED_FEATURES.keys())
    mean = corpus[corpus_cols].mean().values
    std = corpus[corpus_cols].std().replace(0, 1).values

    cz = (corpus[corpus_cols].values - mean) / std
    tz = (tracks[track_cols].astype(float).values - mean) / std

    lean_rows, like_rows = [], []
    for vec in tz:
        dist = np.linalg.norm(cz - vec, axis=1)
        order = np.argsort(dist)
        nearest = corpus.iloc[order[:K_NEIGHBOURS]]
        shares = nearest["genre"].value_counts(normalize=True)
        lean_rows.append({f"lean_{g}": round(float(shares.get(g, 0.0)), 2) for g in GENRES})
        top3 = corpus.iloc[order[:3]]
        like_rows.append({
            "sounds_like": " | ".join(f"{a} – {t} ({g})" for a, t, g in zip(top3["artist"], top3["title"], top3["genre"])),
            "nearest_distance": round(float(dist[order[0]]), 3),
        })

    out = pd.concat([tracks.reset_index(drop=True), pd.DataFrame(lean_rows), pd.DataFrame(like_rows)], axis=1)
    out["genre_lean"] = out[[f"lean_{g}" for g in GENRES]].idxmax(axis=1).str.replace("lean_", "")
    # log_drum_presence saturates at 1.0 on sub-bass-heavy mixes, so check whether the lean survives without it
    without_log_drum = {k: v for k, v in SHARED_FEATURES.items() if k != "log_drum_presence"}
    out["genre_lean_no_log_drum"] = knn_genre_lean(out, corpus, without_log_drum)

    genre_centroids = {g: cz[(corpus["genre"] == g).values].mean(axis=0) for g in GENRES}
    genre_spread = {
        g: float(np.linalg.norm(cz[(corpus["genre"] == g).values] - c, axis=1).mean())
        for g, c in genre_centroids.items()
    }
    space = {"mean": mean, "std": std, "genre_centroids": genre_centroids, "genre_spread": genre_spread}
    return out, space


VERSION_PREFERENCE = {"master": 0, "": 1, "main": 1, "original": 2, "slowed": 3, "unmixed": 4, "demo": 5}


def pick_distinct_songs(tracks: pd.DataFrame) -> pd.DataFrame:
    ranked = tracks.assign(_pref=tracks["version"].map(VERSION_PREFERENCE).fillna(9))
    ranked = ranked.sort_values(["song_group", "_pref", "duration_s"], ascending=[True, True, False])
    return ranked.drop_duplicates("song_group").drop(columns="_pref")


def scaled(df: pd.DataFrame, space: dict) -> np.ndarray:
    return (df[list(SHARED_FEATURES.keys())].astype(float).values - space["mean"]) / space["std"]


def add_artist_position(tracks: pd.DataFrame, space: dict) -> pd.DataFrame:
    """Mark the file that represents each song and score every file's distance from the artist's centre."""
    songs = pick_distinct_songs(tracks)
    centroid = scaled(songs, space).mean(axis=0)
    return tracks.assign(
        in_profile=tracks["file_name"].isin(songs["file_name"]),
        distinctiveness=np.linalg.norm(scaled(tracks, space) - centroid, axis=1).round(3),
    )


def build_profile(artist: str, tracks: pd.DataFrame, space: dict) -> dict:
    songs = tracks[tracks["in_profile"]]
    z = scaled(songs, space)
    centroid = z.mean(axis=0)

    centroid_dist = {g: round(float(np.linalg.norm(centroid - c)), 3) for g, c in space["genre_centroids"].items()}
    nearest_genre = min(centroid_dist, key=centroid_dist.get)
    spread = float(songs["distinctiveness"].mean())

    lane_col = f"lean_{nearest_genre}"

    def describe(col):
        s = songs[col].astype(float)
        return {"median": round(float(s.median()), 3), "p25": round(float(s.quantile(0.25)), 3),
                "p75": round(float(s.quantile(0.75)), 3), "min": round(float(s.min()), 3), "max": round(float(s.max()), 3)}

    return {
        "artist": artist,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine_version": "1.3.0",
        "files_analyzed": int(len(tracks)),
        "distinct_songs": int(len(songs)),
        "signature": {c: describe(c) for c in list(SHARED_FEATURES) + ["energy_rms", "onset_rate", "loudness_lufs", "duration_s"]},
        "lane": {
            "nearest_genre": nearest_genre,
            "centroid_distance": centroid_dist,
            "song_lean_counts": songs["genre_lean"].value_counts().to_dict(),
            "mean_lean": {g: round(float(songs[f"lean_{g}"].mean()), 2) for g in GENRES},
        },
        "cohesion": {
            "artist_spread": round(spread, 3),
            "genre_spread": {g: round(v, 3) for g, v in space["genre_spread"].items()},
            "ratio_to_nearest_genre": round(spread / space["genre_spread"][nearest_genre], 2),
        },
        "standouts": {
            "most_distinct": songs.nlargest(3, "distinctiveness")[["title", "distinctiveness"]].to_dict("records"),
            "most_on_lane": songs.nlargest(3, lane_col)[["title", lane_col]].rename(columns={lane_col: "lean"}).to_dict("records"),
            "highest_groove": songs.nlargest(3, "groove_score")[["title", "groove_score"]].to_dict("records"),
        },
        "robustness": {
            "song_lean_counts_no_log_drum": songs["genre_lean_no_log_drum"].value_counts().to_dict(),
            "lean_unchanged_share": round(float((songs["genre_lean"] == songs["genre_lean_no_log_drum"]).mean()), 2),
        },
        "caveats": caveats(songs),
        "distinct_song_files": songs["file_name"].tolist(),
    }


def caveats(songs: pd.DataFrame) -> list[str]:
    notes = []
    saturated = float((songs["log_drum_presence"] >= 0.99).mean())
    if saturated >= 0.5:
        notes.append(
            f"log_drum_presence is at its 1.0 ceiling on {saturated:.0%} of songs. The measure is driven by sub-bass "
            "share, so heavy modern low end can max it out without a true log drum. Confirm by ear; it also "
            "feeds 20% of the groove score."
        )
    quiet = songs.loc[songs["loudness_lufs"] < -20, "title"].tolist()
    if quiet:
        notes.append(f"Very quiet (likely unmastered) files: {', '.join(quiet)}. Their energy and loudness will read low next to masters.")
    return notes


def write_notes_template(path: Path, tracks: pd.DataFrame) -> None:
    if path.exists():
        log.info(f"Keeping existing listening notes: {path}")
        return
    notes = tracks[["file_name", "title", "song_group"]].copy()
    for col in ["perceived_genre", "energy_1to5", "groove_1to5", "standout", "notes"]:
        notes[col] = ""
    notes.to_csv(path, index=False)
    log.info(f"Wrote listening notes template: {path}")


def run(artist: str) -> Path:
    artist_dir = ARTIST_DATA_DIR / artist
    audio_dir = artist_dir / "audio"
    files = sorted(p for p in audio_dir.iterdir() if p.suffix.lower() in AUDIO_EXTENSIONS)
    if not files:
        raise SystemExit(f"No audio files in {audio_dir}")

    rows = []
    for i, path in enumerate(files, 1):
        log.info(f"[{i}/{len(files)}] {path.name}")
        try:
            rows.append(analyze_file(path))
        except Exception as e:
            log.error(f"Failed on {path.name}: {e}")

    tracks = pd.DataFrame(rows)
    tracks, space = compare_to_corpus(tracks, load_corpus())
    tracks = add_artist_position(tracks, space)
    tracks.to_csv(artist_dir / "tracks.csv", index=False)

    profile = build_profile(artist, tracks, space)
    (artist_dir / "profile.json").write_text(json.dumps(profile, indent=2))
    write_notes_template(artist_dir / "listening_notes.csv", tracks)

    log.info(f"Analyzed {len(tracks)}/{len(files)} files → {artist_dir}")
    return artist_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute an artist's sonic profile")
    parser.add_argument("artist", help="Artist slug, e.g. sikiboi")
    args = parser.parse_args()
    run(args.artist)
