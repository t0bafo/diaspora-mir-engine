# 🧬 Music DNA — Album Playlist Curator

> **An intelligent, culturally-informed playlist curator and similarity engine built on top of [`diaspora-mir-engine`](../README.md)'s audio feature pipeline.**

---

## 1. Overview

**Music DNA** bridges the gap between raw audio DSP feature extraction and consumer-facing music discovery. While standard streaming algorithms rely on Eurocentric beat grids or opaque collaborative-filtering black boxes, Music DNA uses the explicit **8-dimensional acoustic groove vectors** extracted by `diaspora-mir-engine` to:

1. **Calculate Sonic Fingerprints:** Generate album-level centroids and individual track feature vectors that respect polyrhythms, syncopation, and log drum presence.
2. **Harmonic & Rhythmic Similarity:** Match tracks across artists and albums using normalized cosine similarity.
3. **Intelligent Playlist Sequencing:** Chain tracks dynamically using smooth BPM transitions (nearest-neighbor) or narrative energy arcs (build-up → peak → cool-down).
4. **Local-First & Auditable:** Store all metadata and vectors in an embedded SQLite database (`music_dna.db`) and export to standard playlist formats (`.m3u8`, `.json`, `.txt`).

---

## 2. 8-Dimensional Feature Vector

Each track in Music DNA is indexed across an 8-dimensional normalized feature vector:

| Feature Dimension | Extraction Source | Description |
|:---|:---|:---|
| `bpm` | Essentia `RhythmExtractor2013` | Primary tempo estimation |
| `energy_rms` | Audio Waveform RMS | Dynamic loudness and perceived sonic intensity |
| `onset_rate` | Essentia Onset Rate | Density of percussive attacks per second |
| `rhythmic_complexity` | Inter-Onset Interval CV | Non-linear complexity $\tanh(1.5 \times \text{CV})$ |
| `syncopation` | 16th-Note Phase Quantization | Ratio of offbeat onsets to total onsets |
| `pulse_clarity` | Onset Autocorrelation | Metronomic strength of the foundational beat grid |
| `log_drum_presence` | Sub-Bass Ratio + Spectral Centroid | Detection heuristic for the Amapiano FM log drum |
| `danceability_custom` | Culturally-Tuned Metric | Weighted groove metric favoring syncopation and bass |

---

## 3. Architecture & Modules

```
music_dna/
├── __init__.py      # Package metadata and FEATURE_COLUMNS definition
├── database.py      # SQLite storage layer (WAL-mode, foreign keys, query index)
├── ingest.py        # Pipeline for directory scanning & JSON/CSV corpus ingestion
├── similarity.py    # StandardScaler normalization & Cosine Similarity engine
├── playlist.py      # Playlist builder, sequencing algorithms & export formats
└── __main__.py      # Full CLI interface (python -m music_dna <command>)
```

### Module Breakdown

* **`database.py` ([`MusicDNADatabase`](file:///Users/tobafo/.gemini/antigravity/scratch/tech_projects/mir_system/music_dna/database.py#L65)):**  
  Manages relational tables (`artists`, `albums`, `tracks`) and coordinates feature matrix queries. Handles idempotent inserts and fuzzy queries via case-insensitive matching.
* **`ingest.py` ([`ingest_directory`](file:///Users/tobafo/.gemini/antigravity/scratch/tech_projects/mir_system/music_dna/ingest.py#L123), [`import_corpus_json`](file:///Users/tobafo/.gemini/antigravity/scratch/tech_projects/mir_system/music_dna/ingest.py#L246)):**  
  Extracts features on the fly using `analyze_track.py` for raw audio files (`.mp3`, `.wav`, `.flac`, etc.) or bulk-imports precomputed benchmarks like `diaspora_corpus_features_v1_3.json`.
* **`similarity.py` ([`SimilarityEngine`](file:///Users/tobafo/.gemini/antigravity/scratch/tech_projects/mir_system/music_dna/similarity.py#L22)):**  
  Fits scikit-learn's `StandardScaler` on the library matrix to eliminate feature scale disparities, then applies `cosine_similarity`. Supports album centroids, track-to-track distance, and cross-album blends.
* **`playlist.py` ([`Playlist`](file:///Users/tobafo/.gemini/antigravity/scratch/tech_projects/mir_system/music_dna/playlist.py#L46)):**  
  Converts match sets into sequenced playlists:
  - `sequence_by_similarity()`: Strict match order.
  - `sequence_by_bpm()`: Greedy nearest-neighbor chain to eliminate jarring tempo jumps.
  - `sequence_by_energy_arc()`: Tripartite narrative curve (build-up $\rightarrow$ peak $\rightarrow$ resolution).

---

## 4. CLI Usage Guide

Run all commands using the project's virtual environment:

```bash
./venv/bin/python -m music_dna <subcommand> [options]
```

### 1. View Library Statistics
```bash
./venv/bin/python -m music_dna info
```
Output:
```text
  🧬 Music DNA Database: .../music_dna.db
  ─────────────────────────────
  Artists:  126
  Albums:   0
  Tracks:   294
  Genres:   afrobeats, afropiano, amapiano
```

### 2. Import Precomputed Corpus
```bash
./venv/bin/python -m music_dna import-corpus diaspora_corpus_features_v1_3.json
```

### 3. Ingest Local Audio Directory
Scan a directory structured as `Artist/Album/Track.mp3`:
```bash
./venv/bin/python -m music_dna ingest /path/to/music/ --genre amapiano
```

### 4. Search Similar Tracks for an Album
Find tracks across your library that sonically match a reference album:
```bash
./venv/bin/python -m music_dna similar "Amukelani" --limit 15 --sequence bpm
```

### 5. Library-Wide Discovery
Broad discovery around a target album with tempo tolerance:
```bash
./venv/bin/python -m music_dna discover "Amukelani" --bpm-tolerance 5.0 --output discovery.m3u8
```

### 6. Cross-Album Mix
Generate a blended journey between two distinct albums (e.g., transitioning from an Afrobeats project into Private School Amapiano):
```bash
./venv/bin/python -m music_dna mix "Album A" "Album B" --steps 12 --sequence energy -o journey.json
```

### 7. List Entities
```bash
./venv/bin/python -m music_dna list artists
./venv/bin/python -m music_dna list tracks --limit 20
```

---

## 5. Export Formats

Playlists generated by Music DNA can be exported directly:
* **M3U8 (`.m3u` / `.m3u8`):** Industry-standard format compatible with Apple Music, VLC, Rekordbox, and Serato.
* **JSON (`.json`):** Full serialized feature state and scoring metadata for web clients and visualizations.
* **Text (`.txt`):** Plain human-readable track list.
