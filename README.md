# 🌍 diaspora-mir-engine

### A Culturally-Informed Music Information Retrieval (MIR) & Audio DSP Engine for African Diasporic Genres

**Author:** [Tobi Afolayan](https://github.com/t0bafo) — Creative Technologist & Music Tech Researcher  
**Affiliation / Context:** NYU Music Technology / Global Music Studies  
**Status:** Active Exploratory Research & Computational Musicology Prototype (v1.3.0)  
**License:** MIT  

---

## 1. Executive Summary & Research Statement

Mainstream Music Information Retrieval (MIR) systems and commercial streaming algorithms are historically grounded in Eurogenetic music theory. They rely on **isochronous (evenly-spaced) rhythmic baselines** that define "orderly" rhythm as metric regularity, penalizing polyrhythmic density and high syncopation as "chaotic" or "undanceable." 

When applied to African Diasporic genres — such as Nigerian Afrobeats, South African Amapiano, and hybrid Afropiano — commercial audio pipelines break down:
* Chart-topping Amapiano anthems (e.g., TitoM & Yuppe's *Tshwala Bam*) were scored as low as **0.41 in danceability** by commercial APIs, while mid-tempo pop tracks easily scored ~0.80.
* Genre recommenders routinely lump South African Private School Amapiano into four-on-the-floor Berlin minimal techno simply because they share a tempo tier (~112–115 BPM).

**`diaspora-mir-engine`** is an open-source audio DSP engine and computational musicology framework built from scratch to address this systemic algorithmic gap. By engineering transparent, culturally-informed rhythmic and timbral features, the engine extracts the physical signatures of African groove. In blind, unsupervised tests on a 294-track corpus, machine learning algorithms (K-Means) **naturally clustered the tracks into their respective cultural genres with up to 98.7% purity** without ever being shown a label.

---

## 2. Motivation: The Isochronous Bias

In November 2024, Spotify deprecated public access to its audio features endpoint, eliminating outside auditability into how algorithmic scores are assigned. Prior empirical research confirmed that commercial danceability models:
1. **Penalize Rhythmic Complexity:** High variance in Inter-Onset Intervals (IOIs) is treated as a timing error rather than intentional polyrhythmic syncopation.
2. **Conflate Meter with Pulse:** Tracks with straight subdivisions receive higher pulse confidence than tracks featuring layered, cross-rhythmic counterpoints.
3. **Ignore Genre-Defining Timbral Anchors:** The FM-synthesized log drum (originally pioneered via the Fruity DX10 preset by South African producers like MDU aka TRP) is completely unrepresented in Western feature sets.

This engine provides a fully reproducible, local-first alternative where every mathematical transformation is auditable, explainable, and culturally contextualized.

---

## 3. Mathematical Feature Architecture

Rather than black-box embeddings, `diaspora-mir-engine` computes explicit acoustic descriptors directly from audio waveforms (44.1 kHz / 48.0 kHz):

```
Audio Input (WAV / MP3)
      │
      ├── [Essentia C++ RhythmExtractor2013] ──────────→ BPM & Beat Grid
      │
      ├── [NumPy Inter-Onset Interval (IOI)] ─────────→ Rhythmic Complexity: tanh(1.5 · CV)
      │
      ├── [NumPy 16th-Note Phase Quantization] ───────→ Syncopation Ratio (Offbeat Hits)
      │
      ├── [Onset Autocorrelation @ Beat Lag] ─────────→ Pulse Clarity (Internal Metronome)
      │
      ├── [Essentia EnergyBand (30–120Hz) + Centroid] ─→ Log Drum FM Timbral Signature
      │
      └── [Culturally-Tuned Synthesis] ───────────────→ Calibrated Danceability Index
```

### Feature Formulations

1. **Rhythmic Complexity ($C_{IOI}$):**
   Measures the coefficient of variation (CV) of Inter-Onset Intervals, squashed via a non-linear hyperbolic tangent to prevent transient outliers from blowing up the score:
   $$\text{CV} = \frac{\sigma(\text{IOI})}{\mu(\text{IOI})}, \quad C_{IOI} = \tanh(1.5 \times \text{CV})$$
   *Note: In this engine, high complexity is never penalized in groove scoring.*

2. **Syncopation / Offbeat Density ($S_{16}$):**
   For each detected onset at time $t$, its fractional phase relative to the nearest beat is calculated:
   $$\phi = \left(\frac{t - t_{\text{nearest\_beat}}}{\tau_{\text{beat}}}\right) \pmod{1.0}$$
   Onsets falling in the 16th-note offbeat intervals $\phi \in [0.15, 0.35] \cup [0.65, 0.85]$ are classified as syncopations. The metric is the ratio of offbeat to total onsets.

3. **Pulse Clarity ($P_c$):**
   The normalized autocorrelation of the onset strength envelope sampled at the beat period lag ($\pm 2$ frames). This reflects how rigorously the groove locks to its foundational pulse grid.

4. **Log Drum Timbral Signature ($L_D$):**
   Isolates the percussive, pitch-bent sub-bass transient unique to Amapiano by coupling sub-bass energy concentration ($30\text{--}120\text{ Hz}$) with attack-frame spectral centroid:
   $$L_D = 0.70 \times \text{NormSubBassRatio} + 0.30 \times (1.0 - \text{NormOnsetCentroid})$$

5. **Culturally-Tuned Danceability ($D_{\text{cult}}$):**
   Excludes complexity penalties and actively rewards syncopated micro-groove and bass drive:
   $$D_{\text{v1.3.0}} = 0.50 \times P_c + 0.30 \times S_{16} + 0.20 \times L_D$$

---

## 4. Empirical Benchmark Findings

The system was evaluated against a verified **294-track corpus** across three diasporic classes:
* **Afrobeats** (West Africa / Nigeria & Ghana)
* **Amapiano** (South Africa — Private School, Sgija, Bacardi, Vocal)
* **Afropiano** (The contemporary pan-African hybrid sound)

### Unsupervised K-Means Clustering Validation

To test whether the acoustic features correspond to genuine cultural boundaries, an unsupervised K-Means model ($k=3$) was executed on the normalized vector $[C_{IOI}, S_{16}, P_c, L_D]$ **without human genre labels**:

| Cluster | Dominant Genre | Purity | Track Count ($n$) | Avg Syncopation | Avg Pulse Clarity | Avg Log Drum | Avg Danceability |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **0** | **Amapiano (Pure)** | **90.0%** | 60 | 0.460 | 0.773 | 0.868 | 0.708 |
| **1** | **Afropiano Bridge / Private School** | **80.0%** | 80 | 0.347 | 0.746 | 0.980 | 0.673 |
| **2** | **Afrobeats (Pure)** | **98.7%** | 154 | 0.349 | 0.640 | 0.010 | 0.525 |

**Key Takeaways:**
* **98.7% Afrobeats Separation:** The absence of the FM log drum and distinct syncopation dynamics allowed blind separation of pure Afrobeats from South African styles.
* **The "House Backbone" Hypothesis Confirmed:** Amapiano tracks consistently exhibit higher internal pulse clarity (mean 0.773 vs 0.640) than Afrobeats, demonstrating that Amapiano functions as an electronic dance music subgenre anchored to a rigid metronome despite its polyrhythmic surface.

---

## 5. Out-of-Distribution Auditing & NYU GMFT Tools

As part of exploratory research at NYU GMFT, the engine includes auxiliary diagnostic tools in [`nyu_gmft/tools/`](file:///Users/tobafo/.gemini/antigravity/scratch/tech_projects/mir_system/nyu_gmft/tools/) to evaluate domain transfer when the engine is exposed to out-of-distribution (OOD) Western music (e.g., American Indie Rock / Synth-Punk).

* **The Sub-Bass Trap:** In test cases with heavy compressed electric bass guitars and analog synthesizers below 120 Hz (e.g., Mitski's *Why Didn't You Stop Me*), the v1.3.0 log drum heuristic saturated at `1.0000` false-positive. 
* **Insight:** Sub-bass energy + attack centroid is effective within club/electronic African diaspora genres, but requires multi-band harmonic-percussive source separation (HPSS) to prevent confusion with saturated rock/pop bass guitars.

---

## 6. Current Status & Research Roadmap

| Phase | Milestone | Status |
|:---|:---|:---:|
| **Phase 1** | Baseline feature extractor (Librosa + Essentia) & 157 Afrobeats benchmark | Completed |
| **Phase 2** | Curated 226-track Amapiano corpus + cross-genre rhythm metrics | Completed |
| **Phase 3** | v1.3.0 Log Drum FM detector & unsupervised K-Means clustering (294 tracks) | Completed |
| **Phase 4** | Interactive Streamlit data visualization dashboard | Completed |
| **Phase 5** | Auxiliary diagnostics & OOD stress-testing tooling ([`nyu_gmft/tools/`](file:///Users/tobafo/.gemini/antigravity/scratch/tech_projects/mir_system/nyu_gmft/tools/)) | Completed |
| **Phase 6** | Deep neural stem separation (Demucs / Open-Unmix) for isolated log drum timbre | In Progress |
| **Phase 7** | Expansion to broader African Diaspora (Afro-Cuban, Dancehall, Gqom, Batida) | Planned |
| **Phase 8** | Empirical streaming audit: quantifying discovery suppression & economic impact | Planned |

---

## 7. Project Architecture

```
diaspora-mir-engine/
│
├── analyze_track.py                   # Core feature extraction engine (Essentia + Librosa)
├── batch_analyze.py                   # Corpus batch processor with statistical summaries
├── deep_analysis.py                   # K-Means clustering, purity scoring & artist profiling
├── dashboard.py                       # Interactive Streamlit dashboard (2D/3D Plotly)
├── diaspora_corpus_features_v1_3.json # Full 294-track feature matrix (JSON benchmark)
├── requirements.txt                   # Locked Python dependencies
├── AMAPIANO_CRITERIA.md               # Musicological taxonomy & decision tree
├── FINDINGS_v2_05052026.md            # Extended research findings log
│
├── docs/                              # Research documentation & guides
│   ├── RESEARCH_ESSAY.md              # Long-form thesis on algorithmic bias & cultural MIR
│   └── VISUALS_GUIDE.md               # Guide to published benchmark figures
│
├── nyu_gmft/                          # NYU GMFT exploratory analysis & diagnostics
│   └── tools/
│       ├── audio_auxiliary.py         # Advanced auxiliary DSP (HPSS, Chroma key profile, Mid/Side)
│       ├── build_onepager_pdf.py      # Publication-grade ReportLab audit PDF generator
│       └── build_reconstruction_xlsx.py # Openpyxl arrangement timeline generator
│
├── amapiano_corpus/                   # Amapiano corpus metadata & analysis benchmarks
│   ├── amapiano_tracks.csv            # Hand-curated track catalog with subgenre tags
│   └── analysis_v1_3/                 # Batch result figures & tables
│
├── music_dna/                         # Intelligent Album Playlist Curator & Similarity Engine
│   ├── README.md                      # Music DNA documentation and CLI guide
│   ├── database.py                    # SQLite storage layer for track vectors & metadata
│   ├── ingest.py                      # Audio extraction & corpus ingestion pipeline
│   ├── similarity.py                  # Normalized cosine similarity & centroid matching
│   ├── playlist.py                    # BPM & energy-arc playlist sequencing
│   └── __main__.py                    # CLI entrypoint (`python -m music_dna`)
│
├── full_dataset_v1/                   # Phase 1 Afrobeats single-genre benchmark
└── merged_dataset/                    # Phase 3 cross-genre merged benchmark & visuals
```

---

## 8. Installation & Quickstart

### Prerequisites
* **macOS / Linux** with Python 3.10+
* **ffmpeg** installed on host system (`brew install ffmpeg` on macOS, `sudo apt install ffmpeg` on Ubuntu)

### Setup
```bash
# Clone the repository
git clone https://github.com/t0bafo/diaspora-mir-engine.git
cd diaspora-mir-engine

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Usage Examples

**1. Analyze a Single Track:**
```bash
python analyze_track.py path/to/song.mp3 --output results.json
```

**2. Batch Analyze an Audio Directory:**
```bash
python batch_analyze.py path/to/corpus/ --output results/ --default-genre amapiano
```

**3. Run Unsupervised K-Means & Cluster Purity Analysis:**
```bash
python deep_analysis.py results/analysis_results.csv --output results/
```

**4. Launch the Interactive Exploration Dashboard:**
```bash
streamlit run dashboard.py
```

**5. Curate Playlists with Music DNA:**
```bash
# Import benchmark corpus & query similar tracks
python -m music_dna import-corpus diaspora_corpus_features_v1_3.json
python -m music_dna discover "Amukelani" --sequence bpm -o playlist.m3u8
```

---

## 9. Citation

If you reference this work, models, or datasets in your academic research, please cite:

```bibtex
@software{afolayan2026diaspora,
  author = {Afolayan, Tobi},
  title = {diaspora-mir-engine: A Culturally-Informed Music Information Retrieval Engine for African Diasporic Genres},
  year = {2026},
  url = {https://github.com/t0bafo/diaspora-mir-engine},
  institution = {New York University}
}
```

---

## 10. Author & Contact

**Tobi Afolayan**  
Creative Technologist & Music Tech Researcher  
* GitHub: [@t0bafo](https://github.com/t0bafo)  
* Web: [tobiafo.com](https://tobiafo.com)  
