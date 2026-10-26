import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="MIR African Polyrhythm Analysis", layout="wide")

st.title("🎵 African Diaspora MIR System")
st.markdown("### Discovering the Mathematical DNA of Afrobeats and Amapiano")

# ── Load Data
def load_data():
    base_path = Path(__file__).parent
    csv_paths = [
        base_path / "full_dataset_v1/analysis_results.csv",
        base_path / "amapiano_corpus/analysis_v1_3/analysis_results.csv"
    ]
    dfs = []
    for p in csv_paths:
        if p.exists():
            dfs.append(pd.read_csv(p))
            
    if not dfs:
        return pd.DataFrame()
        
    df = pd.concat(dfs, ignore_index=True)
    
    # Ensure log_drum exists and fill legacy NaNs with 0.0
    if "log_drum" not in df.columns:
        df["log_drum"] = 0.0
    df["log_drum"] = df["log_drum"].fillna(0.0)

    # Basic artist/title extraction if standard 'Artist - Title.mp3' format
    df["artist"] = df["file_name"].apply(lambda x: x.split(" - ")[0] if " - " in x else "Unknown")
    df["title"] = df["file_name"].apply(lambda x: x.split(" - ")[1].replace(".mp3", "") if " - " in x else x.replace(".mp3", ""))
    return df

with st.spinner("Loading MIR extraction matrices..."):
    df = load_data()

if df.empty:
    st.warning("Analysis datasets not found. Please wait for `batch_analyze.py` to finish generating the CSVs!")
else:
    # ── Sidebar Filters
    st.sidebar.header("Dataset Filters")
    genres = st.sidebar.multiselect(
        "Select Genres", 
        options=df["genre"].unique(), 
        default=df["genre"].unique()
    )
    
    # NEW: Log Drum Intensity Filter
    st.sidebar.markdown("---")
    min_log = st.sidebar.slider("Minimum Log Drum Intensity", 0.0, 1.0, 0.0, 0.05)
    
    filtered_df = df[(df["genre"].isin(genres)) & (df["log_drum"] >= min_log)]

    # ── High Level Stats
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Tracks", len(filtered_df))
    c2.metric("Avg Rhythmic Complexity", f"{filtered_df['complexity'].mean():.3f}")
    c3.metric("Avg Syncopation", f"{filtered_df['syncopation'].mean():.3f}")
    c4.metric("Avg Log Drum Presence", f"{filtered_df['log_drum'].mean():.3f}")
    c5.metric("Avg Danceability", f"{filtered_df['danceability'].mean():.3f}")

    # ── The Groove Scatter Plot (3D)
    st.markdown("## 🌌 The Groove Signature Map (v1.3.0)")
    st.markdown("Now featuring **Timbral Intelligence**: Filter by 'Log Drum Presence' in the sidebar to see the true architects of the sound.")
    
    fig_3d = px.scatter_3d(
        filtered_df, x='pulse_clarity', y='syncopation', z='complexity',
        color='genre', hover_name='file_name', 
        labels={
            "pulse_clarity": "Pulse Clarity (House Backbone)",
            "syncopation": "Syncopation (Off-beat Grooves)",
            "complexity": "Complexity (Polyrhythmic Density)"
        },
        opacity=0.8,
        color_discrete_map={"amapiano": "#FF5733", "afrobeats": "#33C1FF", "afropiano": "#9B59B6"},
        hover_data=["log_drum", "bpm", "artist"]
    )
    fig_3d.update_traces(marker=dict(size=4))
    fig_3d.update_layout(
        height=700,
        margin=dict(l=0, r=0, b=0, t=0),
        dragmode='orbit',
        scene_dragmode='orbit',
        scene=dict(
            xaxis_title="Pulse Clarity",
            yaxis_title="Syncopation",
            zaxis_title="Complexity"
        )
    )
    st.plotly_chart(fig_3d, use_container_width=True, theme=None)
    
    # ── 2D Scatter
    st.markdown("## 📊 Log Drum vs Danceability")
    fig_2d = px.scatter(
        filtered_df, x="log_drum", y="danceability",
        color="genre", hover_name="file_name",
        color_discrete_map={"amapiano": "#FF5733", "afrobeats": "#33C1FF", "afropiano": "#9B59B6"},
        hover_data=["bpm", "artist"]
    )
    st.plotly_chart(fig_2d, use_container_width=True)

    # ── Data Table
    st.markdown("## 📋 Extracted Math")
    sort_by = st.selectbox("Sort Table By", ["log_drum", "danceability", "syncopation", "complexity", "bpm", "pulse_clarity"])
    st.dataframe(filtered_df[["artist", "title", "genre", "log_drum", "danceability", "syncopation", "complexity", "bpm"]].sort_values(sort_by, ascending=False), use_container_width=True)
