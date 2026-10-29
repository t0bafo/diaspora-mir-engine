# Idea: Song-by-Song Analysis

Status: idea, not started. Nothing here is implemented.
Owner: Tobi Afolayan
Last updated: 2026-10-29

---

## 1. The idea in one paragraph

Today the engine only describes the curated 294-track corpus. The next step is to point it at **any song**: pick a track from my Spotify library (or search for one), get its audio, run `mir_engine` on it, and see where it lands against the corpus: its 8 scores, its position on the Groove Signature Map, and the corpus tracks it sounds closest to. New songs are kept **separate** from the corpus so the research dataset stays clean.

This is also the most natural connection point between this repo and the Music DNA web app (see [`../INTERSECTION.md`](../INTERSECTION.md)): Music DNA knows *which* songs a listener cares about (Spotify), and the MIR engine knows *what they sound like* rhythmically.

## 2. Why

- **The corpus is hand-picked.** It proves the features separate genres, but it can't answer "what about this song I just heard?"
- **Spotify gives no audio and no trustworthy groove numbers.** Its audio-features endpoint is closed to new apps (Nov 2024), and a 2026 *Music Perception* study (Vidas, Nitschinsk, Osborne, Rickard; 244 listeners, 40 excerpts) reported that Spotify's danceability did not track human danceability ratings. (Seen cited in [Designs by Duhart, part 9](https://designsbyduhart.org/blog/danceability-vs-what-rhythm-measures/); read the paper before citing.)
- **It turns a research engine into something usable.** One song in, a readable rhythmic profile out.

## 3. Who it's for

1. **Me, as researcher**: test the engine on songs outside the corpus (new releases, edge cases, out-of-distribution genres like the Mitski audit).
2. **Me, as listener**: understand my own Spotify library through this lens ("which of my liked songs carry a log drum?").
3. **Later, Music DNA users**: optional groove scores on their tracks (see section 10).

## 4. User stories

1. I search a song by title/artist, or pick one from my Spotify liked songs or a playlist, and get its 8 MIR scores.
2. I see where it sits on the 3D Groove Signature Map, drawn with a distinct marker on top of the corpus.
3. I see its 5 nearest corpus tracks, and which genre cluster it falls into.
4. I can analyze a batch (a whole playlist) and browse the results as a table.
5. Every result shows **where the audio came from** (full download vs 30-second preview) and when it was analyzed.
6. Analyzed songs never change the corpus file or the corpus statistics shown on the dashboard.

## 5. How it would flow

```
Spotify (metadata only)          Audio source (swappable)          MIR engine            Storage (separate)
───────────────────────          ────────────────────────          ──────────            ──────────────────
liked songs / playlist /   ──►   find + fetch audio for     ──►    mir_engine     ──►    data/new_songs/
search                           "artist – title"                  8 features            analyses.json
track id, ISRC, title,           check duration vs Spotify         (~4 s/song)           (git-ignored)
artists, duration                                                                              │
                                                                                               ▼
                                                                            Dashboard page: "Analyze a song"
                                                                            scores · map position · nearest tracks
```

### 5.1 Song selection (Spotify)

- Spotify provides metadata only: track id, ISRC, title, artists, album, duration.
- Sources: liked songs, a playlist, or a search query.

### 5.2 Audio source: one swappable step

The audio step is a single replaceable component, so the rest of the pipeline doesn't care where audio comes from.

| Source | Status | Quality | Notes |
| --- | --- | --- | --- |
| **Downloader (yt-dlp / friend's scraper)** | Chosen for now | Full track | Same approach as `scripts/amapiano_downloader.py` (`ytsearch1` by artist + title). **Interim only**, until a licensed source exists. Run on my Mac only. |
| Own audio files (upload) | Possible anytime | Full track | Most accurate, no rights issue. DRM-protected Apple Music / Spotify streams can't be used. |
| 30-second previews (iTunes Search API, Deezer by ISRC) | Tested, works | Partial | Free, no login. Results must be labelled as preview-based. |
| Licensed audio | Goal | Full track | To be figured out; the swap point above makes this a one-place change. |

Matching rule for the downloader: reject a result if its duration differs from Spotify's by more than about 10 seconds (catches live versions, sped-up edits, covers). Log mismatches instead of guessing.

### 5.3 Analysis

- Same `mir_engine` extractor as the corpus, so the numbers are directly comparable.
- About 4 seconds per song on a laptop-class CPU.

### 5.4 Storage: separate from the corpus

- `data/new_songs/analyses.json` (git-ignored), one record per song, keyed by Spotify track id.
- Downloaded audio in `downloads/new_songs/` (already git-ignored); audio can be deleted after analysis.
- The corpus file (`data/corpus/diaspora_corpus_features_v1_3.json`) is never written to.
- Optional later: an explicit "promote to corpus" step, reviewed by hand, with genre labels following `AMAPIANO_CRITERIA.md`.

Proposed record:

```json
{
  "spotify_track_id": "…",
  "isrc": "…",
  "title": "Tshwala Bam",
  "artists": ["TitoM", "Yuppe", "S.N.E", "EeQue"],
  "spotify_duration_ms": 0,
  "audio": {
    "source": "yt-dlp",
    "kind": "full",
    "matched_title": "…",
    "duration_s": 0,
    "duration_delta_s": 0
  },
  "features": {
    "bpm": 0, "energy_rms": 0, "onset_rate": 0,
    "rhythmic_complexity": 0, "syncopation": 0, "pulse_clarity": 0,
    "log_drum_presence": 0, "danceability_custom": 0
  },
  "engine_version": "1.3.0",
  "analyzed_at": "2026-10-29T08:00:00Z"
}
```

### 5.5 Dashboard

A new page in `scripts/dashboard.py`:

- Score card for the selected song.
- The 3D map with the corpus plus new songs as a different marker.
- Nearest corpus tracks (scaled feature distance), and the cluster it falls in.
- Table of all analyzed songs, filterable by audio source.

The **public** Streamlit app only reads saved results. Downloading happens locally; YouTube usually blocks cloud servers, and a public app should not fetch audio.

## 6. Early evidence: a 30-second preview vs the full track

Tested on 2026-10-29 with Apple's public 30-second preview of "Tshwala Bam" (TitoM & Yuppe), compared with the full-track values in the corpus:

| Feature | 30-second preview | Full track (corpus) |
| --- | --- | --- |
| BPM | 111.8 | 111.92 |
| Pulse clarity | 0.845 | 0.799 |
| Syncopation | 0.452 | 0.403 |
| Rhythmic complexity | 0.430 | 0.630 |
| Log drum presence | 1.0 | 0.0 |
| Danceability (custom) | 0.758 | 0.641 |

Takeaways:

- Tempo and pulse survive a short clip; complexity and log drum depend heavily on which 30 seconds you get. Full tracks are preferred, and preview-based results must be labelled.
- **Possible corpus data issue:** the corpus labels this track `afrobeats` with `log_drum` 0.0, while the story video presents it as Amapiano. Worth re-checking the label and the log-drum value for this track.

## 7. Guardrails

- **Rights:** downloading is an interim, personal-research measure. Keep audio local, don't redistribute it, delete it after analysis when possible, and move to a licensed source when available.
- **Corpus integrity:** new songs are never mixed into corpus statistics, clustering, or published findings unless explicitly promoted.
- **Honest labelling:** every result shows its audio source and engine version. `danceability_custom` has not been validated against listener ratings (see section 9).
- **Public app is read-only:** no downloading or analysis triggered from the deployed dashboard.

## 8. Phases

1. **Single song, local**: one command takes "artist – title" or a Spotify track id, fetches audio, analyzes, saves the record.
2. **Dashboard page**: view saved songs, map overlay, nearest tracks.
3. **Spotify library batch**: liked songs or a playlist, with skip-already-analyzed and a mismatch log.
4. **Music DNA bridge**: export analyses keyed by Spotify track id for optional import by Music DNA (no runtime coupling).
5. **Licensed audio**: replace the interim downloader behind the same swap point; re-analyze songs tagged `yt-dlp`.

## 9. Related research thread

Listener validation of `danceability_custom`: a small study (a few dozen people rating 20–40 excerpts) would test whether the culturally-tuned score matches what people feel, which the K-Means genre purity does not show. Until then, consider presenting it as a "groove index" rather than "danceability". Song-by-song analysis would make it easy to assemble the excerpt set.

## 10. Connection to Music DNA

- Shared key: Spotify track id (and ISRC).
- Direction: MIR engine → static export → Music DNA optional import. Music DNA never calls Python at runtime and must work without it.
- Possible later: a small hosted analysis API, only once a licensed audio source exists.

## 11. Open questions

1. Which downloader: `scripts/amapiano_downloader.py` or my friend's scraper (likely the local `afrobeats_scraper/`, not in git)? Fold it into this repo or keep it external?
2. Keep downloaded audio after analysis, or delete it?
3. How should Spotify access work locally: a small sign-in script, or export the list from Music DNA?
4. Should the public dashboard show my analyzed library songs, or only the corpus?
5. What's the bar for "promoting" a new song into the corpus?
6. Licensed audio: which provider or licensing route to explore?
