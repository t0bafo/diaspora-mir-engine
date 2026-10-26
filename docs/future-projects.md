# Future Projects

Ideas to build when ready. Nothing in this file is implemented yet.

---

## Album Mixtapes (Music DNA)

**Status:** Planned, not started
**Added:** Oct 25, 2026 (revised Oct 26, 2026)
**Home:** a feature inside [Music DNA](https://github.com/t0bafo/music-dna), with this repo as an optional audio layer. No new repo is needed.

### Goal

Pick two or more albums from my Spotify library and mix them into one mixtape, so the result feels like a curated tape rather than one album played after another.

### Scope

- **Source:** albums I have saved on Spotify.
- **Unit:** whole albums, with the option to skip tracks.
- **Not used:** ReccoBeats or other third-party audio-feature APIs.
- **Not in scope yet:** automatic discovery of similar albums, new-release alerts, recommendations from listening history. These were in the first draft of this idea and can come back later.

### What already exists

| Need | Already in place |
| --- | --- |
| Spotify login and library access | Music DNA (Spotify OAuth) |
| Holding a draft tracklist and reordering it by hand | Music DNA Crates (drag-and-drop) |
| Saving the result to Spotify | Music DNA export to Spotify |
| Tempo, energy and rhythm features from audio | This repo (`analyze_track.py`) |

### Two kinds of mixtape

| | Playlist mixtape | Audio mixtape |
| --- | --- | --- |
| Result | A Spotify playlist that weaves tracks from 2+ albums | One continuous audio file with transitions |
| Needs audio files | No | Yes, files I own |
| Plays in Spotify | Yes | No |
| Shareable | Yes | Personal use only (rights) |
| Built in | Music DNA | This repo plus an audio tool |

Start with the playlist mixtape. The audio mixtape is a later step.

### Data available from Spotify

For saved albums the Spotify Web API provides the track list, track order, durations, artists, release dates and popularity. It does not provide tempo, key or energy for this app, so ordering has to work from metadata or from audio analysed here.

### Ordering method (metadata only)

Albums have an arc: opener, build, middle, closers. The mix should keep each album's arc instead of playing them back to back.

1. Choose two or more saved albums and drop any tracks to skip.
2. Give each track a relative position on its album from 0 (first track) to 1 (last track).
3. Merge all tracks by relative position, so openers land early, middles in the middle, and closers at the end.
4. Smooth the order:
   - Avoid two tracks in a row from the same album, unless they belong together (for example, a skit leading into a song).
   - Fit a target length, such as 45 minutes, or split into Side A and Side B.
   - Allow pinned tracks, such as "this opener stays first."
5. Save the result as a Crate, adjust by hand, and export to Spotify.

### Optional audio layer (this repo)

For albums I own as audio files, run `analyze_track.py` / `batch_analyze.py` ahead of time and store the results by Spotify track ID. The ordering step can then:

- place tracks with close tempos next to each other,
- shape a deliberate energy curve,
- use the rhythm features (syncopation, pulse clarity, log drum) so genre changes feel intentional,
- use key compatibility, once key output is added (Essentia has a key detector; the engine does not output key yet).

Albums without audio files still work with the metadata-only method.

### Phases

1. **Prototype:** pick albums, generate the merged order, preview as a Crate, export to Spotify.
2. **Controls:** skip tracks, pin tracks, target length, Side A / Side B.
3. **Audio layer:** pre-computed tempo, energy and rhythm features for owned albums, used to smooth transitions.
4. **Audio mixtape (optional):** continuous mixed file from owned audio, for personal use.

### Open questions

- Which two albums to use as the first test case (confirm exact artist and album names).
- Whether an audio mixtape is wanted at all, or only Spotify playlists.
- Default mixtape length, and whether Side A / Side B is the default layout.
- Where to store pre-computed audio features (Music DNA's Supabase database is the likely place).

### Constraints

- Music DNA's Spotify app is in Development Mode, so only manually approved users can sign in.
- Raw audio must never be committed to this repo (see `.gitignore`).
