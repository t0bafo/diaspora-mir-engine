"""
deep_analysis.py — Advanced statistical profiling and clustering for MIR results.

Extracts artist-level signatures and performs K-Means clustering to distinguish
genres (Amapiano, Afrobeats, etc.) based on rhythmic DNA.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import re
import argparse

def extract_artist(file_name):
    """Simple regex to pull artist from 'Artist - Title.mp3' format."""
    # Remove quotes
    name = str(file_name).replace('"', '').replace("'", "")
    # Try split by ' - '
    parts = re.split(r' - | – ', name)
    if len(parts) > 1:
        return parts[0].strip()
    return "Unknown"

def calculate_purity(df):
    """Calculate what percentage of each cluster matches its dominant genre."""
    purity_results = []
    for cluster in sorted(df["cluster"].unique()):
        cluster_df = df[df["cluster"] == cluster]
        total = len(cluster_df)
        if total == 0: continue
        
        counts = cluster_df["genre"].value_counts()
        dominant_genre = counts.index[0]
        dominant_count = counts.iloc[0]
        purity = (dominant_count / total) * 100
        
        purity_results.append({
            "cluster": cluster,
            "dominant_genre": dominant_genre,
            "purity": round(purity, 2),
            "count": total,
            "breakdown": counts.to_dict()
        })
    return purity_results

def perform_clustering(df, n_clusters=3):
    """Discover natural groups using K-Means on groove features."""
    # PHASE 8: Include log_drum as a core feature
    features = ["complexity", "syncopation", "pulse_clarity", "log_drum"]
    
    # Filter to only rows that have all features
    df = df.dropna(subset=features)
    X = df[features]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)
    
    return df, kmeans

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_paths", nargs="+", help="Paths to analysis_results.csv files")
    parser.add_argument("--output", "-o", default="merged_dataset", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    visuals_dir = output_dir / "visuals"
    visuals_dir.mkdir(parents=True, exist_ok=True)

    dfs = [pd.read_csv(p) for p in args.csv_paths]
    df = pd.concat(dfs, ignore_index=True)
    
    # 1. Artist Extraction
    df["artist"] = df["file_name"].apply(extract_artist)
    
    # 2. Artist Profiling (Top 15 artists by track count)
    top_artists = df["artist"].value_counts().head(15).index
    artist_profiles = df[df["artist"].isin(top_artists)].groupby("artist").agg({
        "complexity": "mean",
        "syncopation": "mean",
        "pulse_clarity": "mean",
        "danceability": "mean",
        "bpm": "mean"
    }).sort_values("danceability", ascending=False)
    
    artist_profiles.to_csv(output_dir / "artist_signatures.csv")

    # 3. Clustering
    df, kmeans = perform_clustering(df, n_clusters=3)
    
    # 4. Describe Clusters & Calculate Purity
    purity_stats = calculate_purity(df)
    purity_df = pd.DataFrame(purity_stats)
    
    cluster_desc = df.groupby("cluster").agg({
        "syncopation": "mean",
        "pulse_clarity": "mean",
        "complexity": "mean",
        "log_drum": "mean",
        "danceability": "mean",
        "file_name": "count"
    }).rename(columns={"file_name": "track_count"})
    
    # 5. Visualization: Syncopation vs Pulse Clarity (Cluster Colored)
    plt.figure(figsize=(10, 7))
    sns.scatterplot(
        data=df, x="syncopation", y="pulse_clarity", hue="cluster", 
        palette="viridis", s=100, alpha=0.7
    )
    plt.title("Rhythmic Clusters (Unsupervised): Syncopation vs Pulse Clarity", fontsize=14)
    plt.savefig(visuals_dir / "cluster_scatter_kmeans.png")
    plt.close()

    # 5b. Visualization: Syncopation vs Pulse Clarity (Genre Colored - The Ground Truth)
    if "genre" in df.columns:
        plt.figure(figsize=(10, 7))
        sns.scatterplot(
            data=df, x="syncopation", y="pulse_clarity", hue="genre", 
            palette="Set1", s=100, alpha=0.9
        )
        plt.title("Rhythmic Profiles (Ground Truth): Syncopation vs Pulse Clarity", fontsize=14)
        plt.savefig(visuals_dir / "cluster_scatter_genre.png")
        plt.close()
    
    # 6. Top Results
    top_syncopated = df.sort_values("syncopation", ascending=False).head(10)[["artist", "file_name", "syncopation"]]
    top_danceable = df.sort_values("danceability", ascending=False).head(10)[["artist", "file_name", "danceability", "genre"]]

    # 7. Generate Findings Report
    report = f"""# Deep MIR Analysis Findings — Scientific Validation (v1.3.0)

## Cluster Purity Analysis
This section measures how closely the machine's unsupervised clusters match our "Ground Truth" labels.

{purity_df.to_markdown(index=False)}

---

## Natural Rhythmic Clusters (Physics-Based)
We identified 3 natural "states" of rhythm using Complexity, Syncopation, Pulse Clarity, and Log Drum Intensity.

{cluster_desc.to_markdown()}

---

## Artist Signature Analysis
The top artists in the dataset show distinctive "Groove Signatures":

{artist_profiles.to_markdown()}

## Visualizations
- `visuals/cluster_scatter_genre.png`: The ground truth (how African genres plot mathematically).
- `visuals/cluster_scatter_kmeans.png`: Unsupervised grouping (how the ML model groups them blindly).

## Top 10 Most Danceable Tracks (Amapiano-Agnostic Formula)
{top_danceable.to_markdown(index=False)}

---
*Generated by deep_analysis.py (Phase 8)*
"""
    (output_dir / "FINDINGS.md").write_text(report)
    
    # Save the final labeled dataset for the Diaspora Bias Auditor
    df.to_csv(output_dir / "final_labeled_dataset.csv", index=False)
    
    print(f"✅ Deep analysis complete. Artifacts in {output_dir}/")
    print(f"Review findings: {output_dir}/FINDINGS.md")

if __name__ == "__main__":
    main()
