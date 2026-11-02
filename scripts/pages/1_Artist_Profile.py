"""Artist Profile — one artist's sonic signature, lane, standouts and the ear-vs-numbers check.

Reads <artist>/{tracks.csv, profile.json, listening_notes.csv} written by scripts/artist_profile.py, from a
private GitHub repo or a local folder (mir_engine.artist_store). The page is locked behind a password and
shows nothing when none is configured. Artist data is never committed here; see docs/artist-profile/SPEC.md.

Settings come from the `[artist_dashboard]` section of Streamlit secrets, or from environment variables:
    password        MIR_ARTIST_PASSWORD
    github_repo     MIR_ARTIST_GITHUB_REPO     e.g. t0bafo/artist-data
    github_token    MIR_ARTIST_GITHUB_TOKEN    fine-grained token, Contents read/write on that repo only
    github_branch   MIR_ARTIST_GITHUB_BRANCH   default main
Without a GitHub repo it falls back to MIR_ARTIST_DATA_DIR.
"""

import hmac
import io
import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from mir_engine.artist_store import store_from_settings
from mir_engine.config import ARTIST_DATA_DIR

st.set_page_config(page_title="Artist Profile", layout="wide")

GENRES = ["afrobeats", "amapiano", "afropiano"]
GENRE_COLORS = {"afrobeats": "#E4572E", "amapiano": "#2E86AB", "afropiano": "#A23B72"}
RATED_MIN = 5

# Starting hypotheses for who to pitch to; tempo bands follow docs/artist-profile/SPEC.md story 11
TEMPO_BANDS = [
    ("Slow / mood (< 95 BPM)", 0, 95, "R&B-leaning and late-night mood playlists"),
    ("Afrobeats radio (95–108 BPM)", 95, 108, "Afrobeats radio and mainstream Afro playlists"),
    ("Amapiano DJ sets (108–118 BPM)", 108, 118, "Amapiano DJs, club and dance playlists"),
    ("Up-tempo (≥ 118 BPM)", 118, 999, "Club edits and high-energy DJ sets"),
]


SETTING_KEYS = ["password", "github_repo", "github_token", "github_branch"]


def load_settings() -> dict:
    section = dict(st.secrets.get("artist_dashboard", {})) if st.secrets.load_if_toml_exists() else {}
    return {k: section.get(k) or os.getenv(f"MIR_ARTIST_{k.upper()}", "") for k in SETTING_KEYS}


@st.cache_data(ttl=300, show_spinner=False)
def cached_artists(_store, label: str) -> list[str]:
    return _store.list_artists()


@st.cache_data(ttl=300, show_spinner=False)
def cached_text(_store, label: str, artist: str, name: str) -> str | None:
    return _store.read_text(artist, name)


def unlocked(password: str) -> bool:
    if not password:
        st.info("The artist dashboard is private and not enabled on this deployment.")
        return False
    if st.session_state.get("artist_unlocked"):
        return True
    with st.form("artist_login"):
        attempt = st.text_input("Password", type="password")
        if st.form_submit_button("Unlock"):
            if hmac.compare_digest(attempt.encode(), password.encode()):
                st.session_state["artist_unlocked"] = True
                st.rerun()
            st.error("Wrong password.")
    return False


def tempo_band(bpm: float) -> tuple[str, str]:
    for name, lo, hi, target in TEMPO_BANDS:
        if lo <= bpm < hi:
            return name, target
    return TEMPO_BANDS[-1][0], TEMPO_BANDS[-1][3]


def shortlist(songs: pd.DataFrame, lane: str) -> pd.DataFrame:
    """Songs ranked by how many lead reasons they carry, then groove. Reasons stay visible."""
    top_groove = set(songs.nlargest(5, "groove_score")["file_name"])
    top_distinct = set(songs.nlargest(5, "distinctiveness")["file_name"])
    top_lane = set(songs.nlargest(5, f"lean_{lane}")["file_name"])

    def reasons(r):
        out = []
        if r.file_name in top_groove:
            out.append("top-5 groove")
        if r.file_name in top_distinct:
            out.append("top-5 distinct")
        if r.file_name in top_lane:
            out.append(f"top-5 {lane} fit")
        if r.loudness_lufs is not None and r.loudness_lufs < -20:
            out.append("⚠ unmastered?")
        if r.genre_lean != r.genre_lean_no_log_drum:
            out.append("⚠ lean depends on log drum")
        return out

    s = songs.copy()
    s["reasons"] = s.apply(reasons, axis=1)
    s["n_reasons"] = s["reasons"].apply(lambda rs: sum(not x.startswith("⚠") for x in rs))
    s["reasons"] = s["reasons"].apply(", ".join)
    s[["tempo_band", "pitch_to"]] = s["bpm"].apply(lambda b: pd.Series(tempo_band(b)))
    return s.sort_values(["n_reasons", "groove_score"], ascending=False)


def ear_vs_numbers(notes: pd.DataFrame, tracks: pd.DataFrame) -> dict:
    merged = notes.merge(tracks, on="file_name", suffixes=("", "_t"))
    out = {"rated_genre": 0, "rated_energy": 0, "rated_groove": 0}

    genre = merged[merged["perceived_genre"].astype(str).str.strip().str.lower().isin(GENRES)].copy()
    out["rated_genre"] = len(genre)
    if len(genre):
        perceived = genre["perceived_genre"].str.strip().str.lower()
        out["genre_agreement"] = float((perceived == genre["genre_lean"]).mean())
        out["genre_agreement_no_log_drum"] = float((perceived == genre["genre_lean_no_log_drum"]).mean())
        out["genre_table"] = genre.assign(perceived=perceived)[
            ["title", "perceived", "genre_lean", "genre_lean_no_log_drum"]
        ]

    for rating, computed, key in [("energy_1to5", "energy_rms", "energy"), ("groove_1to5", "groove_score", "groove")]:
        r = pd.to_numeric(merged[rating], errors="coerce")
        pair = pd.DataFrame({"ear": r, "numbers": merged[computed]}).dropna()
        out[f"rated_{key}"] = len(pair)
        if len(pair) >= RATED_MIN:
            out[f"{key}_spearman"] = float(pair["ear"].corr(pair["numbers"], method="spearman"))
    return out


def summary_markdown(profile: dict, lead: pd.DataFrame) -> str:
    sig, lane = profile["signature"], profile["lane"]
    lines = [
        f"# {profile['artist']} — sonic profile",
        f"{profile['distinct_songs']} distinct songs from {profile['files_analyzed']} files. Generated {profile['generated_at']}.",
        "",
        "## Lane",
        f"- Closest corpus genre overall: **{lane['nearest_genre']}**",
        f"- Song-level lean: {lane['song_lean_counts']}",
        f"- Without the log drum feature: {profile.get('robustness', {}).get('song_lean_counts_no_log_drum', 'n/a')}",
        f"- Tempo: median {sig['bpm']['median']:.0f} BPM (middle half {sig['bpm']['p25']:.0f}–{sig['bpm']['p75']:.0f})",
        f"- Cohesion ratio vs {lane['nearest_genre']}: {profile['cohesion']['ratio_to_nearest_genre']} (above 1 = wider range than the genre itself)",
        "",
        "## Lead candidates",
    ]
    for r in lead.head(8).itertuples():
        lines.append(f"- **{r.title}** — {r.bpm:.0f} BPM, {r.key}, groove {r.groove_score:.2f}; {r.reasons}; pitch to: {r.pitch_to}. Sounds like: {r.sounds_like}")
    if profile.get("caveats"):
        lines += ["", "## Caveats"] + [f"- {c}" for c in profile["caveats"]]
    return "\n".join(lines) + "\n"


st.title("🎤 Artist Profile")
st.caption("Per-track MIR computation against the Afrobeats / Amapiano / Afropiano corpus. Numbers are evidence for the ear, not a verdict.")

settings = load_settings()
if not unlocked(settings["password"]):
    st.stop()

store = store_from_settings(settings, ARTIST_DATA_DIR)
try:
    artists = cached_artists(store, store.label) if store else []
except Exception as e:
    st.error(f"Could not read artist data from the {store.label}: {e}")
    st.stop()
if not artists:
    st.info("Unlocked, but no artist data was found. Point the dashboard at the private data repo or folder.")
    st.stop()

artist = st.sidebar.selectbox("Artist", artists)
if st.sidebar.button("Lock"):
    st.session_state.pop("artist_unlocked", None)
    st.rerun()
profile = json.loads(cached_text(store, store.label, artist, "profile.json"))
tracks = pd.read_csv(io.StringIO(cached_text(store, store.label, artist, "tracks.csv")))
for col in ("version",):
    tracks[col] = tracks[col].fillna("")
songs = tracks[tracks["in_profile"]] if "in_profile" in tracks else tracks
sig, lane, coh = profile["signature"], profile["lane"], profile["cohesion"]
nearest = lane["nearest_genre"]

for caveat in profile.get("caveats", []):
    st.warning(caveat)

# --- What am I pitching? -----------------------------------------------------------------
st.header("What am I pitching?")
lean_counts = lane["song_lean_counts"]
no_ld = profile.get("robustness", {}).get("song_lean_counts_no_log_drum", {})
range_word = "a tight, recognisable sound" if coh["ratio_to_nearest_genre"] <= 1 else "a wide range rather than one tight sound"
lean_text = ", ".join(f"{n} {g}" for g, n in sorted(lean_counts.items(), key=lambda kv: -kv[1]))
no_ld_text = ", ".join(f"{n} {g}" for g, n in sorted(no_ld.items(), key=lambda kv: -kv[1]))
st.markdown(
    f"**{artist.title()}** sits closest to **{nearest}** overall, at a median **{sig['bpm']['median']:.0f} BPM** "
    f"(middle half {sig['bpm']['p25']:.0f}–{sig['bpm']['p75']:.0f}). Song by song the catalogue leans **{lean_text}**; "
    f"with the log drum feature removed it leans **{no_ld_text}**. The catalogue is {range_word} "
    f"(spread {coh['ratio_to_nearest_genre']}× that of the {nearest} corpus)."
)
if no_ld and max(no_ld, key=no_ld.get) != max(lean_counts, key=lean_counts.get):
    st.error(
        "The majority lean flips when log drum presence is removed. Treat the Amapiano-vs-Afrobeats call as "
        "**unresolved by the numbers** and settle it by ear in the Ear vs numbers section."
    )

c = st.columns(6)
c[0].metric("Distinct songs", profile["distinct_songs"], f"{profile['files_analyzed']} files", delta_color="off")
c[1].metric("Median BPM", f"{sig['bpm']['median']:.0f}")
c[2].metric("Groove score (unvalidated)", f"{sig['groove_score']['median']:.2f}")
c[3].metric("Syncopation", f"{sig['syncopation']['median']:.2f}")
c[4].metric("Pulse clarity", f"{sig['pulse_clarity']['median']:.2f}")
c[5].metric("Median loudness", f"{sig['loudness_lufs']['median']:.1f} LUFS")

# --- Lane --------------------------------------------------------------------------------
st.header("Lane: where each song leans")
left, right = st.columns([3, 2])
lean_long = songs.melt(id_vars=["title"], value_vars=[f"lean_{g}" for g in GENRES], var_name="genre", value_name="share")
lean_long["genre"] = lean_long["genre"].str.replace("lean_", "")
order = songs.sort_values(f"lean_{nearest}")["title"].tolist()
fig = px.bar(
    lean_long, y="title", x="share", color="genre", orientation="h", color_discrete_map=GENRE_COLORS,
    category_orders={"title": order}, height=max(420, 22 * len(songs)),
    labels={"share": "share of 15 nearest corpus tracks", "title": ""},
)
fig.update_layout(legend=dict(orientation="h", y=1.02, x=0), margin=dict(l=0, r=0, t=30, b=0))
left.plotly_chart(fig, use_container_width=True)

dist = pd.DataFrame({"genre": list(lane["centroid_distance"]), "distance": list(lane["centroid_distance"].values())})
right.plotly_chart(
    px.bar(dist, x="genre", y="distance", color="genre", color_discrete_map=GENRE_COLORS, height=260,
           title="Distance from artist centre to each genre centre (lower = closer)").update_layout(showlegend=False),
    use_container_width=True,
)
flip = songs[songs["genre_lean"] != songs["genre_lean_no_log_drum"]][["title", "genre_lean", "genre_lean_no_log_drum", "log_drum_presence"]]
right.markdown(f"**Songs whose lean flips without log drum** ({len(flip)} of {len(songs)})")
right.dataframe(flip, hide_index=True, use_container_width=True)

# --- Signature -----------------------------------------------------------------------------
st.header("Sonic signature")
scatter = px.scatter(
    songs, x="bpm", y="groove_score", color="genre_lean", color_discrete_map=GENRE_COLORS, hover_name="title",
    size="energy_rms", size_max=22, hover_data=["key", "loudness_lufs", "syncopation", "pulse_clarity", "sounds_like"],
    labels={"groove_score": "groove score (unvalidated)", "genre_lean": "lean"}, height=430,
)
for name, lo, hi, _ in TEMPO_BANDS[1:3]:
    scatter.add_vrect(x0=lo, x1=hi, fillcolor="grey", opacity=0.08, line_width=0, annotation_text=name, annotation_position="top left")
st.plotly_chart(scatter, use_container_width=True)

sig_rows = [
    {"feature": f, **{k: v for k, v in sig[f].items()}}
    for f in ["bpm", "groove_score", "syncopation", "pulse_clarity", "rhythmic_complexity", "log_drum_presence", "energy_rms", "loudness_lufs", "duration_s"]
]
st.dataframe(pd.DataFrame(sig_rows), hide_index=True, use_container_width=True)

# --- Which songs lead? ---------------------------------------------------------------------
st.header("Which songs lead?")
st.caption("Ranked by how many reasons a song carries (groove, distinctiveness, fit to lane), then groove. No single magic score. Pitch targets are starting hypotheses from tempo band.")
lead = shortlist(songs, nearest)
st.dataframe(
    lead[["title", "version", "reasons", "bpm", "key", "groove_score", "distinctiveness", f"lean_{nearest}", "genre_lean", "tempo_band", "pitch_to", "sounds_like", "loudness_lufs"]],
    hide_index=True, use_container_width=True,
    column_config={"sounds_like": st.column_config.TextColumn(width="large"), "reasons": st.column_config.TextColumn(width="medium")},
)

band_counts = lead.groupby(["tempo_band", "genre_lean"]).size().reset_index(name="songs")
st.markdown("**Who am I pitching to?** Songs per tempo band and lean")
st.plotly_chart(
    px.bar(band_counts, x="tempo_band", y="songs", color="genre_lean", color_discrete_map=GENRE_COLORS, height=300,
           category_orders={"tempo_band": [b[0] for b in TEMPO_BANDS]}, labels={"tempo_band": ""}),
    use_container_width=True,
)

# --- Versions ------------------------------------------------------------------------------
groups = tracks.groupby("song_group").filter(lambda g: len(g) > 1)
if len(groups):
    st.header("Versions of the same song")
    st.caption("Only the representative file (master first, then longest) counts toward the profile.")
    st.dataframe(groups[["song_group", "file_name", "version", "in_profile", "bpm", "groove_score", "loudness_lufs"]], hide_index=True, use_container_width=True)

# --- Ear vs numbers ------------------------------------------------------------------------
st.header("Ear vs numbers")
st.caption(
    f"Fill in what you hear, then save. Genre: one of {', '.join(GENRES)}. Energy and groove: 1–5. "
    f"Correlations appear once {RATED_MIN}+ songs are rated; with ~20 songs they are indicative, not proof."
)
notes_text = cached_text(store, store.label, artist, "listening_notes.csv")
notes = pd.read_csv(io.StringIO(notes_text), dtype=str).fillna("") if notes_text else pd.DataFrame()
if len(notes):
    edited = st.data_editor(
        notes, hide_index=True, use_container_width=True, disabled=["file_name", "title", "song_group"],
        column_config={"perceived_genre": st.column_config.SelectboxColumn(options=[""] + GENRES)},
        key="notes_editor",
    )
    if st.button("Save listening notes"):
        store.write_text(artist, "listening_notes.csv", edited.to_csv(index=False), message=f"{artist}: update listening notes")
        cached_text.clear()
        st.success(f"Saved listening notes to the {store.label}")
    ev = ear_vs_numbers(edited, tracks)
    m = st.columns(3)
    if "genre_agreement" in ev:
        m[0].metric("Genre agreement", f"{ev['genre_agreement']:.0%}", f"{ev['genre_agreement_no_log_drum']:.0%} without log drum", delta_color="off")
    else:
        m[0].metric("Genre agreement", "—", "no genres rated yet", delta_color="off")
    for col, key in [(m[1], "energy"), (m[2], "groove")]:
        val = ev.get(f"{key}_spearman")
        col.metric(f"{key.title()}: ear vs numbers (Spearman)", f"{val:+.2f}" if val is not None else "—",
                   f"{ev[f'rated_{key}']} songs rated", delta_color="off")
    if "genre_table" in ev:
        st.dataframe(ev["genre_table"], hide_index=True, use_container_width=True)

# --- Export --------------------------------------------------------------------------------
st.header("Export")
e1, e2 = st.columns(2)
e1.download_button("Summary for a label conversation (.md)", summary_markdown(profile, lead), file_name=f"{artist}_profile_summary.md")
e2.download_button("All tracks (.csv)", tracks.to_csv(index=False), file_name=f"{artist}_tracks.csv")
