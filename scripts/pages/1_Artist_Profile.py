"""Artist Profile — one artist's sonic signature, lane, standouts and the ear-vs-numbers check.

Reads <artist>/{tracks.csv, profile.json, listening_notes.csv, brief.json} written by scripts/artist_profile.py
(brief.json is written by hand), from a private GitHub repo or a local folder (mir_engine.artist_store). The
page is locked behind a password and shows nothing when none is configured. Artist data is never committed
here; see docs/artist-profile/SPEC.md.

Three views of the same data, chosen in the sidebar:
    Executive   one screen for a non-technical reader: one sentence, five questions, the 3-D song map,
                readiness, standing against the genres, lead songs, ownership, evidence drawer.
    Artist      the same map framed for the artist: no verdicts, songs by lane, what is theirs, listening ask.
    Analyst     every computation (the original page).

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

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from mir_engine.artist_store import store_from_settings
from mir_engine.config import ARTIST_DATA_DIR, CORPUS_PATH

st.set_page_config(page_title="Artist Profile", layout="wide")

GENRES = ["afrobeats", "amapiano", "afropiano"]
GENRE_COLORS = {"afrobeats": "#E4572E", "amapiano": "#2E86AB", "afropiano": "#A23B72"}
ARTIST_COLOR = "#111111"
RATED_MIN = 5

# Starting hypotheses for who to pitch to; tempo bands follow docs/artist-profile/SPEC.md story 11
TEMPO_BANDS = [
    ("Slow / mood (< 95 BPM)", 0, 95, "R&B-leaning and late-night mood playlists"),
    ("Afrobeats radio (95–108 BPM)", 95, 108, "Afrobeats radio and mainstream Afro playlists"),
    ("Amapiano DJ sets (108–118 BPM)", 108, 118, "Amapiano DJs, club and dance playlists"),
    ("Up-tempo (≥ 118 BPM)", 118, 999, "Club edits and high-energy DJ sets"),
]
# Coarser bands for the executive and artist views
MAP_BANDS = [("under 90", 0, 90), ("90–100", 90, 100), ("100–110", 100, 110), ("110–120", 110, 120), ("120+", 120, 999)]

# Track column -> corpus column, for the 6 features both share (same as scripts/artist_profile.py)
SHARED_FEATURES = {
    "bpm": "bpm", "syncopation": "syncopation", "pulse_clarity": "pulse_clarity",
    "rhythmic_complexity": "complexity", "log_drum_presence": "log_drum", "groove_score": "danceability",
}
# Plain-language names for non-technical views
PLAIN = {
    "bpm": "Tempo", "groove_score": "Groove", "syncopation": "Swing",
    "pulse_clarity": "Beat steadiness", "rhythmic_complexity": "Rhythmic variety",
}
READINESS_ORDER = ["Released", "Mastered, unreleased", "Mixed, needs master", "Demo / pre-master"]
READINESS_COLORS = {"Released": "#9E9E9E", "Mastered, unreleased": "#2E7D32", "Mixed, needs master": "#2E86AB", "Demo / pre-master": "#E9A23B"}

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


@st.cache_data(show_spinner=False)
def load_corpus() -> pd.DataFrame:
    data = json.loads(CORPUS_PATH.read_text())
    return pd.DataFrame(data["all_tracks"]).dropna(subset=list(SHARED_FEATURES.values()))


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


def map_band(bpm: float) -> str:
    return next(name for name, lo, hi in MAP_BANDS if lo <= bpm < hi)


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


# --- Comparative computations for the executive and artist views ----------------------------------------

def readiness_state(row, released: set[str]) -> str:
    if row.file_name in released:
        return "Released"
    lufs = row.loudness_lufs
    if lufs is None or pd.isna(lufs):
        return "Mixed, needs master"
    if lufs >= -10:
        return "Mastered, unreleased"
    if lufs >= -16:
        return "Mixed, needs master"
    return "Demo / pre-master"


def with_readiness(songs: pd.DataFrame, brief: dict) -> pd.DataFrame:
    released = set(brief.get("released", []))
    s = songs.copy()
    s["readiness"] = s.apply(lambda r: readiness_state(r, released), axis=1)
    s["band"] = s["bpm"].apply(map_band)
    return s


def genre_percentiles(songs: pd.DataFrame, corpus: pd.DataFrame) -> pd.DataFrame:
    """Percentile of the artist's song median inside each corpus genre, per shared feature."""
    rows = []
    for tc, cc in SHARED_FEATURES.items():
        med = songs[tc].astype(float).median()
        row = {"feature": tc, "median": med}
        for g in GENRES:
            vals = corpus.loc[corpus["genre"] == g, cc].astype(float).values
            row[g] = float((vals < med).mean() * 100)
        rows.append(row)
    return pd.DataFrame(rows)


def standard_space(corpus: pd.DataFrame):
    cols = list(SHARED_FEATURES.values())
    mean = corpus[cols].mean().values
    std = corpus[cols].std().replace(0, 1).values
    return mean, std


def artist_spreads(songs: pd.DataFrame, corpus: pd.DataFrame, artist: str, min_tracks: int = 5) -> pd.DataFrame:
    """Mean distance from own centroid, in standardised space, for corpus artists with enough tracks plus this artist."""
    mean, std = standard_space(corpus)
    cz = (corpus[list(SHARED_FEATURES.values())].values - mean) / std
    rows = []
    for name, grp in corpus.groupby("artist"):
        if len(grp) < min_tracks or name == "Unknown":
            continue
        z = cz[grp.index.values]
        rows.append({"artist": f"{name} ({len(grp)})", "spread": float(np.linalg.norm(z - z.mean(axis=0), axis=1).mean()), "is_artist": False})
    sz = (songs[list(SHARED_FEATURES.keys())].astype(float).values - mean) / std
    rows.append({"artist": f"{artist.title()} ({len(songs)})", "spread": float(np.linalg.norm(sz - sz.mean(axis=0), axis=1).mean()), "is_artist": True})
    return pd.DataFrame(rows).sort_values("spread")


def two_lanes(songs: pd.DataFrame) -> bool:
    low, high = (songs["bpm"] < 100).mean(), (songs["bpm"] >= 110).mean()
    return low >= 0.3 and high >= 0.3


# --- Figures ----------------------------------------------------------------------------------------------

def fig_song_map_3d(songs: pd.DataFrame, corpus: pd.DataFrame, artist: str, label_songs: bool = True) -> go.Figure:
    """The artist's songs among the corpus, on three interpretable axes. Genre centroids as diamonds."""
    fig = go.Figure()
    for g in GENRES:
        c = corpus[corpus["genre"] == g]
        fig.add_trace(go.Scatter3d(
            x=c["bpm"], y=c["pulse_clarity"], z=c["syncopation"], mode="markers", name=f"{g} ({len(c)} corpus records)",
            marker=dict(size=3, color=GENRE_COLORS[g], opacity=0.35),
            text=c["artist"] + " – " + c["title"], hovertemplate="%{text}<br>%{x:.0f} BPM · steadiness %{y:.2f} · swing %{z:.2f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter3d(
            x=[c["bpm"].mean()], y=[c["pulse_clarity"].mean()], z=[c["syncopation"].mean()], mode="markers", name=f"{g} centre",
            marker=dict(size=9, color=GENRE_COLORS[g], symbol="diamond", line=dict(color="white", width=1)),
            hovertemplate=f"{g} centre<extra></extra>", showlegend=False,
        ))
    hover = (
        songs["title"] + "<br>" + songs["bpm"].round(0).astype(int).astype(str) + " BPM · " + songs["key"].astype(str)
        + " · " + songs["loudness_lufs"].astype(str) + " LUFS<br>leans " + songs["genre_lean"]
    )
    fig.add_trace(go.Scatter3d(
        x=songs["bpm"], y=songs["pulse_clarity"], z=songs["syncopation"], mode="markers+text" if label_songs else "markers",
        name=f"{artist.title()} ({len(songs)} songs)", text=songs["title"] if label_songs else None, textposition="top center",
        textfont=dict(size=10, color=ARTIST_COLOR), customdata=hover,
        marker=dict(size=7, color=ARTIST_COLOR, line=dict(color="white", width=1.5)),
        hovertemplate="%{customdata}<extra></extra>",
    ))
    fig.update_layout(
        height=640, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=0.02, x=0),
        scene=dict(
            xaxis_title="Tempo (BPM)", yaxis_title="Beat steadiness (pulse clarity)", zaxis_title="Swing (syncopation)",
            camera=dict(eye=dict(x=1.55, y=-1.65, z=0.9)),
        ),
    )
    return fig


def fig_readiness(songs: pd.DataFrame) -> go.Figure:
    counts = songs.groupby(["band", "readiness"]).size().reset_index(name="songs")
    fig = px.bar(
        counts, x="band", y="songs", color="readiness", color_discrete_map=READINESS_COLORS,
        category_orders={"band": [b[0] for b in MAP_BANDS], "readiness": READINESS_ORDER},
        labels={"band": "Tempo band (BPM)", "songs": "Songs", "readiness": ""}, height=320,
    )
    fig.update_layout(legend=dict(orientation="h", y=1.12, x=0), margin=dict(l=0, r=0, t=10, b=0), bargap=0.25)
    return fig


def fig_standing_radar(pcts: pd.DataFrame) -> go.Figure:
    feats = ["bpm", "groove_score", "syncopation", "pulse_clarity", "rhythmic_complexity"]
    sub = pcts.set_index("feature").loc[feats]
    cats = [PLAIN[f] for f in feats] + [PLAIN[feats[0]]]
    fig = go.Figure()
    for g in ["afrobeats", "amapiano"]:
        vals = sub[g].tolist() + [sub[g].iloc[0]]
        fig.add_trace(go.Scatterpolar(r=vals, theta=cats, fill="toself", name=f"as an {g} act", line=dict(color=GENRE_COLORS[g]), opacity=0.75))
    fig.add_trace(go.Scatterpolar(r=[50] * len(cats), theta=cats, name="genre middle", line=dict(color="#888", dash="dot"), hoverinfo="skip"))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="%", tickvals=[25, 50, 75, 100])),
        legend=dict(orientation="h", y=-0.1, x=0), height=360, margin=dict(l=30, r=30, t=20, b=10),
    )
    return fig


def fig_spread(spreads: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        spreads, x="spread", y="artist", orientation="h", color="is_artist",
        color_discrete_map={True: ARTIST_COLOR, False: "#BDBDBD"}, height=max(260, 30 * len(spreads)),
        labels={"spread": "Catalogue spread (lower = tighter sound)", "artist": ""}, text=spreads["spread"].round(2),
    )
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
    fig.update_traces(textposition="outside")
    return fig


def fig_lane_donut(lane_counts: dict) -> go.Figure:
    fig = px.pie(names=list(lane_counts), values=list(lane_counts.values()), hole=0.6, color=list(lane_counts),
                 color_discrete_map=GENRE_COLORS, height=220)
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
    fig.update_traces(textinfo="label+value", textposition="outside")
    return fig


# --- Shared page chrome -----------------------------------------------------------------------------------

def big_answer(label: str, answer: str, note: str = ""):
    st.markdown(
        f"<div style='font-size:0.8rem;color:#777;text-transform:uppercase;letter-spacing:.04em'>{label}</div>"
        f"<div style='font-size:1.25rem;font-weight:600;line-height:1.25;margin:.15rem 0'>{answer}</div>"
        f"<div style='font-size:0.85rem;color:#666'>{note}</div>",
        unsafe_allow_html=True,
    )


def lane_label(bpm: float) -> str:
    if bpm >= 108:
        return "Dance records"
    if bpm >= 90:
        return "Songs"
    return "Outside the lanes"


# --- Views -------------------------------------------------------------------------------------------------

def render_executive(artist, profile, tracks, songs, brief, corpus):
    sig, lane, coh = profile["signature"], profile["lane"], profile["cohesion"]
    nearest = lane["nearest_genre"]
    ready = with_readiness(songs, brief)
    unreleased = ready[ready["readiness"] != "Released"]
    n_ready = int((unreleased["readiness"] == "Mastered, unreleased").sum())
    lead = shortlist(songs, nearest)
    pcts = genre_percentiles(songs, corpus)

    st.title(artist.title())
    st.caption(
        f"{profile['distinct_songs']} songs analysed · {int((ready['readiness'] == 'Released').sum())} already released · "
        f"{'ear check pending' if not brief.get('ear_checked') else 'ear check done'} · engine {profile.get('engine_version', '')}"
    )

    one_line = brief.get("one_line") or (
        f"{artist.title()} sits closest to {nearest} overall at a median {sig['bpm']['median']:.0f} BPM, with "
        f"{'two distinct tempo lanes' if two_lanes(songs) else 'one tempo lane'} and a catalogue spread "
        f"{coh['ratio_to_nearest_genre']}× that of the {nearest} corpus."
    )
    st.info(one_line)

    questions = brief.get("questions") or [
        {"q": "What is this?", "a": "Two lanes" if two_lanes(songs) else f"A {nearest} act", "note": f"spread {coh['ratio_to_nearest_genre']}× the genre"},
        {"q": "What is ready?", "a": f"{n_ready} of {len(unreleased)} unreleased", "note": "finished by loudness"},
        {"q": "What leads?", "a": ", ".join(lead.head(3)["title"]), "note": "by groove, fit and distinctness"},
        {"q": "Who is it for?", "a": tempo_band(sig["bpm"]["median"])[1].split(" and ")[0], "note": "from the median tempo"},
        {"q": "What is owned?", "a": "Not in the data", "note": "add to brief.json"},
    ]
    cols = st.columns(len(questions))
    for col, q in zip(cols, questions):
        with col:
            big_answer(q["q"], q["a"], q.get("note", ""))

    st.markdown("")
    st.subheader(f"{artist.title()}'s {len(songs)} songs among {len(corpus)} released records")
    st.plotly_chart(fig_song_map_3d(songs, corpus, artist), use_container_width=True)
    st.caption(
        "Drag to rotate. Each faint dot is a released Afrobeats, Amapiano or Afropiano record; diamonds mark each genre's centre. "
        f"Black dots are {artist.title()}'s songs. Axes: tempo, how steady the beat is, how much swing is in the hits."
    )

    left, right = st.columns([3, 2])
    with left:
        st.subheader("How finished the catalogue is")
        st.plotly_chart(fig_readiness(ready), use_container_width=True)
        st.caption("Finished is judged by loudness: releases sit around −8 to −10 LUFS, mixes at −11 to −16, demos below. Released songs come from the brief.")
    with right:
        st.subheader("Standing against each genre")
        st.plotly_chart(fig_standing_radar(pcts), use_container_width=True)
        st.caption("Percentile of the artist's typical song inside each genre's records. 50% is the genre's middle; 100% means above every record in it.")

    st.subheader("Songs that lead, and why")
    leads = brief.get("leads") or [
        {"title": r.title, "lane": lane_label(r.bpm), "why": r.reasons or "top of the shortlist", "pitch_to": r.pitch_to}
        for r in lead.head(6).itertuples()
    ]
    state_by_title = dict(zip(ready["title"], ready["readiness"]))
    bpm_by_title = dict(zip(ready["title"], ready["bpm"]))
    for row_start in range(0, len(leads), 3):
        cols = st.columns(3)
        for col, item in zip(cols, leads[row_start:row_start + 3]):
            with col, st.container(border=True):
                state = state_by_title.get(item["title"], "")
                bpm = bpm_by_title.get(item["title"])
                st.markdown(f"**{item['title']}**  \n<span style='color:#666'>{item.get('lane', '')}{f' · {bpm:.0f} BPM' if bpm else ''}</span>", unsafe_allow_html=True)
                if state:
                    st.markdown(f"<span style='background:{READINESS_COLORS[state]};color:white;padding:2px 8px;border-radius:10px;font-size:.8rem'>{state}</span>", unsafe_allow_html=True)
                st.write(item.get("why", ""))
                if item.get("pitch_to"):
                    st.caption(f"Pitch to: {item['pitch_to']}")

    if any(k in brief for k in ("ownership", "recommendation", "falsifier")):
        c1, c2, c3 = st.columns(3)
        with c1, st.container(border=True):
            st.markdown("**Ownership**")
            for o in brief.get("ownership", []):
                st.markdown(f"- **{o['item']}:** {o['today']}")
        with c2, st.container(border=True):
            st.markdown("**Recommendation**")
            st.write(brief.get("recommendation", ""))
        with c3, st.container(border=True):
            st.markdown("**What would change this**")
            st.write(brief.get("falsifier", ""))

    with st.expander("Evidence, for anyone who asks how we know"):
        e1, e2 = st.columns([3, 2])
        with e1:
            st.markdown("**Catalogue spread against artists with 5+ records in the corpus**")
            st.plotly_chart(fig_spread(artist_spreads(songs, corpus, artist)), use_container_width=True)
        with e2:
            st.markdown("**Song-level lean**")
            st.plotly_chart(fig_lane_donut(lane["song_lean_counts"]), use_container_width=True)
            no_ld = profile.get("robustness", {}).get("song_lean_counts_no_log_drum", {})
            if no_ld:
                st.caption(f"Without the log-drum feature: {', '.join(f'{n} {g}' for g, n in no_ld.items())}.")
        for caveat in profile.get("caveats", []):
            st.caption(caveat)
        st.caption("Per-song numbers and the method are in the Analyst view.")


def render_artist(artist, profile, tracks, songs, brief, corpus, store):
    ready = with_readiness(songs, brief)
    st.title(f"{artist.title()} — your {len(songs)} songs, mapped")
    st.caption(
        f"Every file in the folder went through the same measurements as {len(corpus)} released Afrobeats, Amapiano and "
        "Afropiano records. This is what the numbers hear. You decide what is true."
    )
    one_line = brief.get("artist_one_line") or (
        f"You make {'two kinds of record' if two_lanes(songs) else 'one kind of record'}: "
        + ", ".join(f"{n} {lab.lower()}" for lab, n in ready["bpm"].apply(lane_label).value_counts().items()) + "."
    )
    st.info(one_line)

    st.subheader(f"Your songs among {len(corpus)} released records")
    st.plotly_chart(fig_song_map_3d(songs, corpus, artist), use_container_width=True)
    st.caption("Drag to rotate. Faint dots are released records, coloured by genre; diamonds are each genre's centre; black dots are yours.")

    st.subheader("How finished each one is")
    st.plotly_chart(fig_readiness(ready), use_container_width=True)
    st.caption("Judged by loudness. Releases sit around −8 to −10 LUFS, mixes at −11 to −16, demos below. Already-released songs are grey.")

    st.subheader("Your songs, by lane")
    notes = brief.get("lane_notes", {})
    groups = [("Dance records", "dance", "110–120 BPM"), ("Songs", "song", "90–108 BPM"), ("Outside the lanes", "outliers", "under 90 BPM")]
    cols = st.columns(3)
    for col, (label, key, sub) in zip(cols, groups):
        grp = ready[ready["bpm"].apply(lane_label) == label].sort_values("bpm", ascending=False)
        with col, st.container(border=True):
            st.markdown(f"**{label}**  \n<span style='color:#666'>{sub} · {len(grp)} songs</span>", unsafe_allow_html=True)
            if len(grp):
                st.markdown(", ".join(grp["title"]))
            if notes.get(key):
                st.caption(notes[key])

    if brief.get("ownership"):
        st.subheader("What is yours")
        st.table(pd.DataFrame(brief["ownership"]).rename(columns={"item": "", "today": "Today", "meaning": "What it means"}).set_index(""))

    st.subheader("Your turn")
    st.write(
        "For each song, tell us what you hear: which lane, how much energy, how much groove, and whether it is one of your "
        "standouts. Where your ear and the numbers disagree, the numbers are the ones that get questioned."
    )
    render_notes_editor(artist, tracks, store, key="artist_notes")


def render_notes_editor(artist, tracks, store, key: str):
    notes_text = cached_text(store, store.label, artist, "listening_notes.csv")
    notes = pd.read_csv(io.StringIO(notes_text), dtype=str).fillna("") if notes_text else pd.DataFrame()
    if not len(notes):
        return None
    edited = st.data_editor(
        notes, hide_index=True, use_container_width=True, disabled=["file_name", "title", "song_group"],
        column_config={"perceived_genre": st.column_config.SelectboxColumn(options=[""] + GENRES)},
        key=key,
    )
    if st.button("Save listening notes", key=f"{key}_save"):
        store.write_text(artist, "listening_notes.csv", edited.to_csv(index=False), message=f"{artist}: update listening notes")
        cached_text.clear()
        st.success(f"Saved listening notes to the {store.label}")
    return edited


def render_analyst(artist, profile, tracks, songs, store):
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
    edited = render_notes_editor(artist, tracks, store, key="notes_editor")
    if edited is not None:
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


# --- Page ---------------------------------------------------------------------------------------------------

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
view = st.sidebar.radio("View", ["Executive", "Artist", "Analyst"], help="Executive: one screen, plain words. Artist: the map framed for the artist. Analyst: every computation.")
if st.sidebar.button("Lock"):
    st.session_state.pop("artist_unlocked", None)
    st.rerun()

profile = json.loads(cached_text(store, store.label, artist, "profile.json"))
tracks = pd.read_csv(io.StringIO(cached_text(store, store.label, artist, "tracks.csv")))
for col in ("version",):
    tracks[col] = tracks[col].fillna("")
songs = tracks[tracks["in_profile"]] if "in_profile" in tracks else tracks
brief_text = cached_text(store, store.label, artist, "brief.json")
brief = json.loads(brief_text) if brief_text else {}

if view == "Analyst":
    st.title("🎤 Artist Profile")
    st.caption("Per-track MIR computation against the Afrobeats / Amapiano / Afropiano corpus. Numbers are evidence for the ear, not a verdict.")
    render_analyst(artist, profile, tracks, songs, store)
else:
    corpus = load_corpus()
    if view == "Executive":
        render_executive(artist, profile, tracks, songs, brief, corpus)
    else:
        render_artist(artist, profile, tracks, songs, brief, corpus, store)
