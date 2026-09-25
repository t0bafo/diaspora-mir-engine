# 🎵 MIR System — *Music DNA*

### A Culturally-Informed Music Information Retrieval Engine for the African Diaspora

> **TL;DR:** Western music algorithms think Amapiano isn't danceable. We built the math to prove them wrong — and the unsupervised clustering agreed with us before we told it anything.

---

## What This Actually Is

Alright, so here's the deal.

Spotify's audio features API — before they [killed public access in November 2024](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api) — would score a TitoM & Yuppe *Tshwala Bam* (one of the biggest Amapiano records on the planet) at **0.41 danceability**. Meanwhile, a mid-tempo Ed Sheeran track sits comfortably at ~0.80. Kelvin Momo's meticulously produced Private School Amapiano gets lumped in the same recommendation bucket as four-on-the-floor Berlin deep house. That's not a quirk — that's a **systemic bias baked into the math**.

The problem is structural: mainstream MIR systems use **isochronous (evenly-spaced) rhythm models** as their baseline for "good" rhythm. Syncopation gets penalized. Polyrhythmic complexity gets penalized. The exact things that *make* Afrobeats and Amapiano groove are the things the algorithm punishes.

**This project is a from-scratch MIR engine that fixes that.**

We built custom feature extractors, a culturally-informed danceability formula, ran unsupervised machine learning on 294 tracks across 3 genre classes — and the blind K-Means clustering **naturally rediscovered** the genre boundaries that musicologists draw by ear. No labels fed in. The physics just... agreed.

---

## The Stack (For the Engineers)

| Layer | Tech | Purpose |
|-------|------|---------|
| **Audio DSP** | [Essentia](https://essentia.upf.edu/) (C++ bindings) + Librosa fallback | Feature extraction at 44.1kHz |
| **ML / Stats** | scikit-learn, NumPy, SciPy, pandas | K-Means clustering, StandardScaler, statistical profiling |
| **Visualization** | Streamlit + Plotly (3D interactive), Matplotlib, Seaborn | Dashboard & publication figures |
| **Data Acquisition** | yt-dlp, BeautifulSoup4, SQLite, custom scrapers | Automated corpus building from blogs + YouTube |
| **Presentation** | Remotion (React 19 + TypeScript + D3.js + Tailwind v4) | 90-second programmatic video at 1080p/30fps |
| **Audio Codec** | ffmpeg | MP3/M4A/FLAC decoding |
| **Runtime** | Python 3.10+ / Node 18+ | Everything runs locally, no cloud dependencies |

---

## The Feature Set — What We Actually Measure

Here's where it gets interesting. We don't use Spotify's black-box features. Every metric is computed from raw audio waveforms with transparent, auditable math:

### 1. Rhythmic Complexity
The coefficient of variation of Inter-Onset Intervals, passed through a nonlinear squash:

```
CV = σ(IOI) / μ(IOI)
Complexity = tanh(1.5 × CV)
```

Filters out micro-noise intervals (<20ms). The `tanh` saturates extreme values so one weird transient doesn't blow up your score. This measures how *irregular* the rhythmic texture is — and crucially, **we don't penalize it**.

### 2. Syncopation (16th-Note Offbeat Density)
For each onset, we compute its phase position relative to the nearest beat:

```
phase = ((t - t_nearest_beat) / median_beat_period) mod 1.0
```

If the phase falls in `[0.15, 0.35]` or `[0.65, 0.85]` — the 16th-note offbeat zones — it counts as a syncopated hit. Syncopation = ratio of offbeat onsets to total onsets. This is *the* metric that Western systems get wrong by treating it as noise.

### 3. Pulse Clarity
Normalized autocorrelation of the onset strength envelope at the beat lag:

```
lag = (sr / hop_length) × (60 / BPM)
pulse_clarity = max(ACF[lag ± 2 frames])
```

This measures how strongly the audio "locks" to its own beat grid. Amapiano has a *house music backbone* — even under layers of polyrhythmic complexity, there's a metronomic pulse underneath. This metric captures that.

### 4. Log Drum Signature (v1.3.0)
The **defining** timbral marker of Amapiano — the FM-synthesized log drum (originally the Fruity DX10 preset, pioneered by MDU aka TRP). We detect it by combining:

- **Sub-bass energy ratio**: Energy in 30–120 Hz vs. full spectrum (30–20kHz) using `EnergyBand`
- **Attack spectral centroid**: Sampled *specifically at onset frames* (not averaged over time), so we isolate the woody percussive transient

```
Log Drum Score = 0.70 × norm_sub_bass_ratio + 0.30 × (1.0 - norm_centroid)
```

Deep bass + low-centroid attacks = log drum. This single feature is why Cluster 2 in our K-Means achieves **98.7% Afrobeats purity** — Afrobeats simply doesn't have log drums.

### 5. Culturally-Tuned Danceability
Two formula versions, both deliberately **excluding complexity as a penalty**:

```
v1.2.1:  Danceability = 0.60 × Pulse Clarity + 0.40 × Syncopation
v1.3.0:  Danceability = 0.50 × Pulse Clarity + 0.30 × Syncopation + 0.20 × Log Drum
```

The philosophical move: syncopation and polyrhythmic density are *features* of groove in African diasporic music, not bugs. The formula rewards them.

---

## Project Architecture

```
mir_system/
│
├── analyze_track.py          # Core feature extraction engine (Essentia + Librosa)
├── batch_analyze.py           # Batch processing, CSV export, auto-generated reports
├── deep_analysis.py           # K-Means clustering, purity analysis, artist fingerprinting
├── dashboard.py               # Streamlit interactive 3D/2D data explorer
├── music_dna.json             # Full 294-track feature matrix (v1.3.0)
├── requirements.txt           # Python dependencies
├── transcribe.sh              # Whisper-based audio transcription utility
│
├── afrobeats_scraper/         # Automated multi-source acquisition engine
│   ├── automated_scraper.py   #   Main orchestrator (parallel scrape → download → extract)
│   ├── trending_song_scraper.py #   Blog + chart scrapers (TrendyBeatz, TooXclusive, etc.)
│   ├── multi_source_downloader.py # 6-tier download fallback chain
│   ├── ai_metadata_extractor.py #   Offline AI feature extraction (37 Spotify-equivalent fields)
│   ├── database.py            #   SQLite persistence layer (songs.db)
│   ├── config.py              #   Scraper configuration & tuning
│   └── tests/                 #   Test suite
│
├── amapiano_corpus/           # Curated South African Amapiano dataset
│   ├── amapiano_tracks.csv    #   226 hand-curated tracks (2018–2026) with subgenre tags
│   ├── amapiano_downloader.py #   yt-dlp batch downloader with resume + confidence filtering
│   ├── download_log.csv       #   Download audit trail
│   └── analysis_v1_3/         #   v1.3.0 batch results (137 tracks)
│       ├── analysis_results.csv
│       └── *.png              #   Scatter, boxplot, KDE visualizations
│
├── full_dataset_v1/           # Phase 1 benchmark: 157 Afrobeats tracks (v1.2.1)
│   ├── analysis_results.csv
│   ├── README.md              #   Auto-generated batch report
│   └── deep_analysis/         #   Initial single-genre clustering & findings
│
├── merged_dataset/            # Phase 8 culmination: 294 tracks, 3 genres, log drum integrated
│   ├── FINDINGS.md            #   Full statistical report + cluster purity tables
│   ├── final_labeled_dataset.csv
│   ├── artist_signatures.csv  #   Per-artist acoustic fingerprints
│   └── visuals/               #   K-Means vs ground-truth scatter plots
│
├── music-dna-story/           # Remotion programmatic video (React 19 + D3 + Tailwind v4)
│   ├── src/
│   │   ├── Composition.tsx    #   5-scene narrative assembly (TransitionSeries)
│   │   ├── Scene1Hero.tsx     #   Tshwala Bam spotlight: Spotify 0.41 vs Music DNA 0.64
│   │   ├── Scene2Waveform.tsx #   Animated frequency spectrum (log drum / perc / piano)
│   │   ├── Scene3SplitScreen.tsx # Algorithm vs Diaspora Engine confrontation
│   │   ├── Scene4Constellation.tsx # D3 scatter: 294 tracks, Amapiano separates live
│   │   ├── Scene5Outro.tsx    #   Stats + wordmark + tagline
│   │   ├── data.json          #   Embedded 294-track dataset for frontend rendering
│   │   └── types.ts           #   TypeScript interfaces
│   └── package.json           #   Remotion v4.0.457 + dependencies
│
├── MIR Story Assets/          # Editorial narrative drafts
│   ├── story_draft.txt        #   Long-form investigative essay on algorithmic bias
│   └── visuals_guide.txt      #   Visualization placement guide for presentation
│
├── AMAPIANO_CRITERIA.md       # Genre taxonomy & classification decision tree
├── FINDINGS_v2_05052026.md    # v2 research findings (316 tracks, May 2026)
├── nyu_gmft/                  # [NEW] — context incoming
└── downloads/                 # Sample audio files
```

---

## The Results — Why This Matters

### Unsupervised Clustering Validates the Culture

We ran K-Means (k=3) on the normalized feature vector `[complexity, syncopation, pulse_clarity, log_drum]` with **zero genre labels**. The algorithm had no idea what Amapiano or Afrobeats even is. Here's what it found:

| Cluster | Dominant Genre | Purity | n | Syncopation | Pulse Clarity | Log Drum | Danceability |
|---------|---------------|--------|---|-------------|---------------|----------|-------------|
| 0 | **Amapiano** | **90.0%** | 60 | 0.460 | 0.773 | 0.868 | 0.708 |
| 1 | Amapiano (Private School / Afropiano bridge) | 80.0% | 80 | 0.347 | 0.746 | 0.980 | 0.673 |
| 2 | **Afrobeats** | **98.7%** | 154 | 0.349 | 0.640 | 0.010 | 0.525 |

**98.7% Afrobeats purity.** The math separated the genres blind. That's not a tuned classifier — that's physics agreeing with culture.

### The Danceability Correction

Under our formula, the most danceable tracks in the corpus are:

| Rank | Track | Artist | Score |
|------|-------|--------|-------|
| 1 | Sukakude | Kelvin Momo ft. Babalwa M | 0.799 |
| 2 | The Grass is Greener | Mr JazziQ | 0.799 |
| 3 | Lawuleka | MDU aka TRP ft. Kabza De Small | 0.797 |
| 4 | Soul To Soul | Kelvin Momo | 0.795 |
| 5 | Story To Tell | De Mthuda | 0.793 |

Every single top-10 entry is Amapiano. Under Spotify's old formula, most of these would score in the 0.3–0.5 range. Under ours, they dominate. The math isn't doing anything magical — it's just *not punishing syncopation*.

### Artist-Level Acoustic Fingerprints

The system produces per-artist groove signatures. Some highlights:

- **Kelvin Momo** (Private School Amapiano): Pulse Clarity **0.836** — the tightest house-music backbone in the dataset. Jazz Rhodes voicings over an unwavering 112.5 BPM grid.
- **Shallipopi** (Nigerian Afrobeats): Syncopation **0.519** — highest in the entire corpus. The swing is the whole point.
- **Wizkid** (Afrobeats): Pulse Clarity **0.594** — the signature Afrobeats "float" where the rhythm drifts more organically off-grid.

---

## The Corpus

**294 tracks** across 3 genre classes, built in phases:

| Phase | Corpus | Tracks | Key Addition |
|-------|--------|--------|-------------|
| 1 | Afrobeats only | 157 | Baseline feature extraction (v1.2.1) |
| 2 | + Amapiano | 316 | Cross-genre clustering, syncopation validation |
| 3 | Merged + timbral | 294 | Log drum detection (v1.3.0), verified & deduplicated |

### Genre Taxonomy (from `AMAPIANO_CRITERIA.md`)

We wrote a full classification decision tree:

```
Step 1 — BPM:     108–118 → Step 2    |    120–130 → Afro-house (unless log drum + piano → afropiano)
Step 2 — Harmony:  Electric piano/jazz synth → Step 3    |    Absent → flag as sgija subgenre
Step 3 — Log Drum: Syncopated FM log drum lead → Step 4    |    Absent → exclude (deep house)
Step 4 — Structure: 5+ min, build-and-layer → AMAPIANO    |    <4 min, verse-chorus → AFROPIANO
```

**The Rhythmic Anchor Rule:** *"If the core pulse is 112 BPM with a syncopated log drum, it is Amapiano regardless of the vocalist's nationality. If it is a 3-minute pop song with a 105 BPM Afropop groove and a log drum added for flavor, it remains Afrobeats."*

Amapiano subgenres tracked: `private_school`, `sgija`, `mozambique`, `bacardi`, `tech_amapiano`, `vocal`, `instrumental`.

---

## Data Acquisition Pipeline

The `afrobeats_scraper/` is a full production scraping engine:

```
Discovery (TrendyBeatz / TooXclusive / NaijaMusic blogs)
    ↓
SQLite dedup check (songs.db, UNIQUE(artist, title))
    ↓
6-tier download fallback:
    JustNaija → TrendyBeatz → TooXclusive → NaijaMusic → Audiomack → YouTube (yt-dlp)
    ↓
File validation: must exist, >1MB, duration 90s–900s
    ↓
AI metadata extraction (37 Spotify-equivalent fields, fully offline via Librosa + Mutagen)
    ↓
Incremental CSV export + HTML report generation
```

Runs as a daemon with 6-hour scrape intervals. No Spotify API dependency — everything is computed from raw audio.

The `amapiano_corpus/` side has a separate `amapiano_downloader.py` targeting YouTube via `yt-dlp`, reading from a hand-curated 226-track CSV spanning 2018–2026 with confidence levels and subgenre tags.

---

## The Video (music-dna-story/)

A **90-second programmatic motion graphics piece** built with Remotion — because the story deserves more than a PDF.

| Scene | Duration | What Happens |
|-------|----------|-------------|
| 1 — Hero | 15s | *Tshwala Bam* spotlight. Animated counters: Spotify 0.41 → Music DNA 0.64 |
| 2 — Waveform | 20s | Three animated SVG frequency layers: sub-bass log drum, percussion, Rhodes |
| 3 — Split Screen | 15s | Left: "The Algorithm" (Spotify). Right: "The Diaspora Engine" (us). +0.33 delta. |
| 4 — Constellation | 20s | D3 scatter of all 294 tracks. At frame 200, Amapiano lifts off into its own golden cluster. |
| 5 — Outro | 20s | Stats, wordmark, *"Built for the music the algorithm missed"* |

Full HD 1920×1080, 30fps, cross-fade transitions between scenes.

---

## Running It

### Feature Extraction (Single Track)
```bash
python analyze_track.py path/to/track.mp3 --output results.json
```

### Batch Analysis
```bash
python batch_analyze.py path/to/audio/folder/ --output results/ --default-genre amapiano
```

### Deep Analysis (Clustering + Findings)
```bash
python deep_analysis.py results/analysis_results.csv --output results/
```

### Interactive Dashboard
```bash
streamlit run dashboard.py
```

### Video Render
```bash
cd music-dna-story/
npm install
npx remotion render MusicDNA out/music-dna.mp4
```

### Setup
```bash
# System dependency
brew install ffmpeg

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## What We're Actually Onto

Let me be real about what this project is building toward.

**The immediate contribution** is a proof-of-concept that African diasporic music has a distinct, measurable mathematical topology — and that mainstream music tech infrastructure systematically misrepresents it. We have the data, the formulas, and the unsupervised validation to back that claim.

**The bigger picture** is about who gets to define the math that music platforms run on. Every recommendation algorithm, every playlist generator, every A&R analytics dashboard, every sync licensing search tool — they all inherit the same Western-centric feature assumptions. When the features are wrong, everything downstream is wrong: discovery, royalties, cultural classification, market sizing.

This system is a working alternative. It's not theoretical — it processes real audio, produces real metrics, and those metrics align with how actual listeners and musicologists understand these genres.

**The business angle:** If you can mathematically distinguish Amapiano from Afrobeats from Afropiano — and you can prove mainstream platforms can't — you have a positioning argument for:
- Genre-specific recommendation engines
- Culturally-informed A&R analytics
- Bias auditing tools for streaming platforms
- Sync licensing search that actually understands sub-Saharan African music
- Label/distributor analytics for the fastest-growing music markets on Earth

**The academic angle:** Computational musicology paper material. Unsupervised clustering achieving 90–98% genre purity on a culturally contested corpus, with transparent feature engineering and a reproducible pipeline.

---

## Current Status (September 2026)

- ✅ Core extraction engine (v1.3.0) with timbral log drum detection
- ✅ 294-track verified corpus across 3 genre classes
- ✅ Unsupervised clustering with 90–98.7% purity
- ✅ Interactive Streamlit dashboard
- ✅ Automated scraping + download pipeline
- ✅ 90-second Remotion video presentation
- ✅ Genre taxonomy + classification decision tree
- ✅ Artist-level acoustic fingerprinting
- 🔲 `nyu_gmft/` — *incoming*

---

## Dependencies

**Python 3.10+**: `essentia==2.1b6.dev1110`, `librosa==0.10.2`, `numpy==1.26.4`, `scipy==1.13.1`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `streamlit==1.35.0`, `plotly==5.22.0`, `tqdm==4.66.4`, `mutagen==1.47.0`, `soundfile==0.12.1`, `audioread==3.0.1`

**Node 18+** (for video): `remotion@4.0.457`, `react@19.2.3`, `d3@7.9.0`, `tailwindcss@4.0.0`

**System**: `ffmpeg` (via Homebrew)

---

*Built by someone who got tired of the algorithm not hearing what the culture already knows.*
