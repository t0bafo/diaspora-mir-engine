# diaspora-mir-engine and Music DNA

Two separate projects. Neither depends on the other, and nothing in this repo is part of the Music DNA app.

| | diaspora-mir-engine (this repo) | Music DNA ([t0bafo/music-dna](https://github.com/t0bafo/music-dna)) |
| --- | --- | --- |
| What it is | Research engine: culturally-informed audio features for Afrobeats, Amapiano, Afropiano | Consumer web app: Spotify-connected taste profile, crates, playlist tools |
| Runs on | Local Python (Essentia, Librosa), Streamlit dashboard, Remotion story app | Lovable / React + Supabase in the browser |
| Input | Audio files you own | Spotify library via OAuth |
| Features | 8 MIR features computed from waveforms (`mir_engine.FEATURE_COLUMNS`) | ReccoBeats audio features (bpm, energy, danceability, valence) |

## Where they could meet later

These are ideas, not commitments. None are implemented.

1. **Feature import.** Export MIR features keyed by Spotify track id as a static JSON file that Music DNA can optionally import (for example, to show syncopation or log-drum presence on tracks it recognizes). Music DNA must keep working without it, and it should never call Python at runtime.
2. **Showcase.** `apps/diaspora-mir-story` can be embedded or linked from Music DNA as a research story, using exported video or data, not shared code.
3. **Shared vocabulary.** If both ever show "danceability", label which one it is (ReccoBeats vs. culturally-tuned `danceability_custom`) so users are not comparing different scales.

## History

An album playlist curator (`packages/music_dna`) briefly lived in this repo. It was removed because album mixtapes belong in the Music DNA app; its ideas were rewritten as a requirements spec for that app.
