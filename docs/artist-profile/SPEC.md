# Artist Sonic Profile — Spec

Status: pilot in progress (first artist: **Sikiboi**).
Owner: Tobi Afolayan
Branch: `cursor/sikiboi-artist-profile-5295`
Last updated: 2026-11-01

---

## 1. Idea

An artist manager has a folder of an artist's songs (released, demos, unmixed, collaborations) and has to make calls about them: what to pitch, who to pitch it to, which records lead, what the artist "is". Those calls are usually made by ear.

The idea: run every song through the MIR engine, build a **sonic profile** of the artist (per track and as a whole), and place it against the 294-track Afrobeats / Amapiano / Afropiano corpus. Then check whether the numbers agree with what a trained ear hears. If they do, the profile becomes evidence a manager can put in front of a label, a DJ or a playlist curator.

This pilot is a **test of that idea**, not a product launch.

## 2. The question this pilot answers

1. **Does the computation match what I hear?** Per track, do tempo, groove, log drum and genre lean line up with my listening notes?
2. **If yes, what decisions can it support?** Genre positioning, lead-single candidates, reference "sounds like" tracks for pitches, and gaps in the catalogue.

If the answer to 1 is no for some features, that is a useful result too: it tells us which numbers not to use in front of a label.

## 3. Users

- **Tobi (analyst):** runs the pipeline, listens, records notes, interprets.
- **Artist manager:** reads the dashboard, uses it to plan pitches and releases.
- **Later, label / A&R or DJs:** receive a one-page summary pulled from the dashboard.

## 4. User stories

### Analyst
1. As the analyst, I point the pipeline at the artist's Drive folder and every track is downloaded into private cloud storage, never into the public repo and never onto my laptop.
2. As the analyst, I get the engine's 8 features for every track, plus duration, key and loudness, in one table.
3. As the analyst, I record my own listening notes per track (perceived genre, energy, danceability, standout yes/no) and the dashboard shows where the numbers agree or disagree with my ear.
4. As the analyst, I can see which files are versions of the same song (demo, unmixed, master, slowed) so they don't double-count in the profile.

### Manager
5. As the manager, I see the artist's **sonic signature** in one view: typical tempo range, groove, log drum use, and how consistent the catalogue is.
6. As the manager, I see where the artist sits between Afrobeats, Amapiano and Afropiano, and which individual songs lean which way.
7. As the manager, for each song I get the 3 closest corpus tracks ("sounds like"), so a pitch can say "in the lane of X and Y".
8. As the manager, I see which songs stand out (highest groove, most distinct, most on-genre) as candidates for singles or for specific playlists and DJs.
9. As the manager, I can export a short summary (per track and overall) for a label conversation.

### Decision support (what the manager is really asking)
10. "What am I pitching?" The dashboard states the artist's lane in plain words, backed by numbers and reference tracks.
11. "Who am I pitching to?" Genre lean and tempo band point to the right labels, DJs and playlists (for example Amapiano DJ sets at 110–115 BPM vs Afrobeats radio at 95–105 BPM).
12. "Which songs lead?" A ranked shortlist with the reasons (groove, distinctiveness, fit to lane), not a single magic score.

## 5. What we compute

### 5.1 Per track
| Field | Source | Notes |
| --- | --- | --- |
| BPM, energy (RMS), onset rate | `mir_engine` | Standard measures |
| Rhythmic complexity, syncopation, pulse clarity | `mir_engine` | Groove features |
| Log drum presence | `mir_engine` | Amapiano signifier |
| Groove score (`danceability_custom`) | `mir_engine` | Shown as "groove score"; not yet validated against listeners |
| Duration, key and scale, integrated loudness (LUFS) | Essentia, in the pipeline script | Key helps DJs and pitching; loudness flags unmastered files |
| Version tag | File name | `demo`, `unmixed`, `master`, `slowed`, `original`, or blank |
| Genre lean | Nearest corpus tracks | Share of the 15 nearest corpus tracks per genre |
| Sounds like | Nearest corpus tracks | Top 3 by scaled distance over the 6 shared features |

The engine analyzes the first 120 seconds of each file, the same as the corpus, so values are comparable.

### 5.2 Artist level
- **Signature:** median and spread of each feature across distinct songs (one version per song).
- **Lane:** overall genre lean, and the corpus genre the artist's centroid is closest to.
- **Cohesion:** how tightly the songs cluster compared with the spread inside each corpus genre. High cohesion = a clear sound; low = a range (not good or bad, but it changes the pitch).
- **Standouts:** songs furthest from the artist's own centroid (distinct) and closest to a genre centroid (on-lane).

### 5.3 Ear vs numbers (the validation loop)
- A listening-notes CSV per track: `perceived_genre`, `energy_1to5`, `groove_1to5`, `standout`, `notes`.
- Dashboard shows: genre agreement (perceived vs computed lean), and rank correlation (Spearman) of energy and groove ratings against the computed values.
- With ~20 songs, correlations are indicative, not proof. The report says so.

## 6. What we build

1. **Ingest:** `scripts/artist_ingest.py` downloads a Google Drive folder into the artist's private data directory.
2. **Compute:** `scripts/artist_profile.py` analyzes every audio file and writes `tracks.csv` and `profile.json` to the same directory, plus a `listening_notes.csv` template if one doesn't exist.
3. **Dashboard:** a new Streamlit page, "Artist Profile", that reads the artist data directory and shows sections 5.1–5.3.

### Storage and privacy
- The repo is public. Audio, track titles and results stay **out of git**.
- Artist data lives in a private persistent cloud store, set by `MIR_ARTIST_DATA_DIR` (default for the pilot: the agent's persistent store, `sikiboi/`).
- Layout: `<data dir>/<artist>/audio/`, `tracks.csv`, `profile.json`, `listening_notes.csv`.
- The public Streamlit app shows "no artist data configured" unless the directory is set. Sharing the dashboard with the manager needs a private deployment (open question 3).

## 7. Out of scope (pilot)
- Lyrics, vocals, language, streaming numbers, social data.
- Commercial predictions ("this will chart").
- Changing the corpus. Artist tracks are never added to it.

## 8. Risks and honest limits
- **The groove score is unvalidated.** It is labelled as such and never presented as "danceability".
- **Demos and unmixed files** analyze differently from masters (loudness, sometimes log drum). Version tags keep them visible.
- **The corpus is the yardstick.** It covers Afrobeats, Amapiano, Afropiano only; songs outside those lanes will look like poor fits rather than "new".
- **Known corpus issue:** at least one corpus track appears mislabelled (see `docs/ideas/song-by-song-analysis.md`). Nearest-track references should be sanity-checked by ear.
- **Rights:** the artist's audio is shared with us privately for analysis. It is not redistributed and not committed.

## 9. Phases
1. **Pilot (this branch):** ingest, compute, dashboard for Sikiboi. Analyst fills listening notes.
2. **Review with the manager:** what was useful, what was noise, which decisions it informed.
3. **Generalize:** any artist folder in, one-page PDF summary out.
4. **Validation:** collect listening notes from more people to test the groove score properly.

## 10. Open questions
1. Which songs are the current release priorities, and which are already out?
2. Are any files duplicates of the same song under different names?
3. How should the manager view it: a private Streamlit deployment, a PDF, or a screen share?
4. What lanes is the manager already considering (Amapiano, Afrobeats, Afro-house, other)?
5. Should collaborations (DJ features) count toward the artist's signature, or be shown separately?
