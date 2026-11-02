# Future Projects

The single index of ideas for this repo, including ideas that belong in another project. Nothing listed here is implemented unless its status says so.

- Short ideas live here as an entry.
- Ideas that grow into a full write-up get their own file in [`ideas/`](ideas/) (or a spec folder) and keep a one-line entry here that links to it.
- Ideas that belong to another project keep an entry here saying where they live, so they aren't lost or rebuilt in the wrong repo.

| Idea | Status | Lives in | Details |
| --- | --- | --- | --- |
| Song-by-song analysis | Idea, documented | This repo (+ Music DNA as a consumer) | [`ideas/song-by-song-analysis.md`](ideas/song-by-song-analysis.md) |
| Artist sonic profile (Sikiboi pilot) | Pilot in progress, not merged | This repo | [PR #4](https://github.com/t0bafo/diaspora-mir-engine/pull/4) |
| Demo check for A&R (compare a new production to the artist's profile) | Idea, from manager feedback | This repo | [`artist-profile/SPEC.md` §11](artist-profile/SPEC.md#11-pilot-feedback) |
| MIR ↔ Music DNA data contract | Idea | Both (shared data, not shared code) | [Entry below](#mir--music-dna-data-contract) and [`INTERSECTION.md`](INTERSECTION.md) |
| Album mixtapes | Planned, not started | **Music DNA** | [Entry below](#album-mixtapes) |

---

## MIR ↔ Music DNA data contract

**Status:** Idea, not started

The two projects should talk through data, not code. A shared table (for example in Music DNA's Supabase) holds analysis requests and results keyed by Spotify track id. A worker on a machine with this repo picks up requests, runs the MIR engine, and writes features back. Music DNA keeps working when no results exist. The contract (table names, columns, feature versions) would be written down before either side builds against it. See [`INTERSECTION.md`](INTERSECTION.md) for the wider picture.

## Album mixtapes

**Status:** Planned, not started
**Lives in:** [Music DNA](https://github.com/t0bafo/music-dna). This repo is at most an optional audio layer.

Pick two or more saved Spotify albums and weave them into one mixtape that keeps each album's arc (openers early, closers late), then save it as a Crate and export to Spotify. The full requirements spec was written for the Music DNA repo (`docs/specs/album-mixtapes.md` there).

What this repo could contribute later: tempo, energy, key and rhythm features for albums owned as audio files, keyed by Spotify track id, to smooth transitions. That would go through the data contract above, not by importing code.

History: an album curator briefly lived in this repo (`packages/music_dna`) and was removed for this reason; see [`INTERSECTION.md`](INTERSECTION.md).
