"""
batch_analyze.py — Batch processing and visual reporting for the MIR system.

Recursively scans a directory for audio files, extracts features using
analyze_track.py logic, and generates a CSV + visual report.

Usage:
    python batch_analyze.py test_tracks/ [--output analysis_report]
"""

import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

# Import core extraction logic from analyze_track
import analyze_track

def discover_files(directory: Path):
    """Recursively find all audio files in directory."""
    audio_files = []
    for ext in analyze_track.SUPPORTED_EXTENSIONS:
        audio_files.extend(list(directory.rglob(f"*{ext}")))
        audio_files.extend(list(directory.rglob(f"*{ext.upper()}")))
    return sorted(list(set(audio_files)))

def process_batch(files: list, manifest_file: Path = None, default_genre: str = None):
    """Run analysis on a list of files and return a list of result dicts."""
    results = []
    
    manifest_data = []
    if manifest_file and manifest_file.exists():
        df_manifest = pd.read_csv(manifest_file)
        for _, row in df_manifest.iterrows():
            manifest_data.append({
                "artist": str(row.get("artist", "")).lower(),
                "title": str(row.get("title", "")).lower(),
                "genre": str(row.get("genre_tag", ""))
            })
            
    print(f"Analysing {len(files)} tracks...")
    
    for i, f in enumerate(tqdm(files, desc="Batch Analysis")):
        try:
            # We bypass the CLI of analyze_track and call its internal functions
            features = analyze_track.extract_features(f)
            res_envelope = analyze_track.build_result(f, features)
            
            # ... [genre logic remains same] ...
            genre = None
            if manifest_data:
                file_stem = f.stem.lower()
                for m in manifest_data:
                    if m["artist"] in file_stem and m["title"] in file_stem:
                        genre = m["genre"]
                        break
            if not genre:
                genre = default_genre if default_genre else (f.parent.name if f.parent.name != "test_tracks" else "default")

            flat_res = {
                "file_name": res_envelope["file_name"],
                "genre": genre,
                "bpm": res_envelope["features"]["tempo_bpm"],
                "energy": res_envelope["features"]["energy_rms"],
                "onset_rate": res_envelope["features"]["onset_rate_per_second"],
                "complexity": res_envelope["features"]["groove"]["rhythmic_complexity"],
                "syncopation": res_envelope["features"]["groove"]["syncopation"],
                "pulse_clarity": res_envelope["features"]["groove"]["pulse_clarity"],
                "log_drum": res_envelope["features"]["groove"]["log_drum_presence"],
                "danceability": res_envelope["features"]["groove"]["danceability_custom"],
                "backend": res_envelope["metadata"]["backend"]
            }
            results.append(flat_res)
            
            # Incremental save every 10 tracks
            if (i + 1) % 10 == 0:
                pd.DataFrame(results).to_csv("amapiano_corpus/analysis_v1_3/analysis_results.csv", index=False)
                
        except Exception as e:
            print(f"\n[ERROR] Failed to process {f.name}: {e}")
            
    return results

def generate_visuals(df: pd.DataFrame, output_dir: Path):
    """Generate comparison plots."""
    sns.set_theme(style="whitegrid")
    
    # 1. Syncopation vs Complexity Scatter
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=df, x="syncopation", y="complexity", hue="genre", 
        style="genre", s=100, alpha=0.8
    )
    plt.title("Rhythmic Profile: Syncopation vs. Complexity", fontsize=14)
    plt.xlabel("Syncopation (Off-beat Emphasis)", fontsize=12)
    plt.ylabel("Complexity (IOI Variability)", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_dir / "syncopation_vs_complexity.png")
    plt.close()

    # 2. Danceability Bar Chart
    plt.figure(figsize=(10, 6))
    order = df.groupby("genre")["danceability"].median().sort_values(ascending=False).index
    sns.boxplot(data=df, x="genre", y="danceability", palette="viridis", order=order)
    plt.title("Danceability Comparison (v1.2.1 Formula)", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_dir / "danceability_comparison.png")
    plt.close()
    
    # 3. Pulse Clarity Density
    plt.figure(figsize=(10, 6))
    for genre in df["genre"].unique():
        subset = df[df["genre"] == genre]
        sns.kdeplot(subset["pulse_clarity"], label=genre, fill=True, alpha=0.3)
    plt.title("Pulse Clarity Distribution by Genre", fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "pulse_clarity_dist.png")
    plt.close()

def generate_report(df: pd.DataFrame, output_dir: Path):
    """Generate a Markdown report."""
    stats = df.groupby("genre")[["bpm", "complexity", "syncopation", "pulse_clarity", "log_drum", "danceability"]].mean()
    
    report = f"""# MIR Batch Analysis Report
    
Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
Total Tracks: {len(df)}
Genres: {', '.join(df['genre'].unique())}

## Genre Statistics (Means)

{stats.to_markdown()}

## Interpretation
- **Amapiano** typically shows higher **Syncopation**, **Log Drum Intensity**, and **Complexity** than Standard Pop.
- **Pulse Clarity** and **Log Drum Presence** are the strongest drivers of the v1.3.0 Danceability score.
- Tracks with high syncopation (>0.3) but low pulse clarity are often complex/polyrhythmic but might have a 'loose' groove.

## Visualizations
![Syncopation vs Complexity](syncopation_vs_complexity.png)
![Danceability Comparison](danceability_comparison.png)
![Pulse Clarity Distribution](pulse_clarity_dist.png)

---
*Results generated by analyze_track.py v1.3.0*
"""
    (output_dir / "README.md").write_text(report)

import datetime

def main():
    parser = argparse.ArgumentParser(description="Batch Analyze MIR Dataset")
    parser.add_argument("directory", help="Directory containing audio files")
    parser.add_argument("--output", "-o", help="Output directory name (default: timestamped)")
    parser.add_argument("--label", "-l", help="Custom label for the report title")
    parser.add_argument("--manifest", help="Optional CSV manifest mapping artist/title to genre_tag")
    parser.add_argument("--default-genre", help="Optional fallback genre if manifest match fails")
    args = parser.parse_args()

    input_dir = Path(args.directory)
    
    # Create distinctive output folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = args.output if args.output else f"analysis_run_{timestamp}"
    output_dir = Path(folder_name)
    output_dir.mkdir(exist_ok=True)

    if not input_dir.exists():
        print(f"Error: Directory {input_dir} not found.")
        sys.exit(1)

    files = discover_files(input_dir)
    if not files:
        print("No supported audio files found.")
        sys.exit(0)

    manifest_path = Path(args.manifest) if args.manifest else None
    results = process_batch(files, manifest_file=manifest_path, default_genre=args.default_genre)
    if not results:
        print("No features extracted.")
        sys.exit(1)

    df = pd.DataFrame(results)
    
    # Final cleanup of genre labels for the report
    if args.label:
        df["run_label"] = args.label

    df.to_csv(output_dir / "analysis_results.csv", index=False)
    
    print(f"Generating visuals and report in {output_dir}/...")
    generate_visuals(df, output_dir)
    generate_report(df, output_dir)
    
    print(f"\n✅ Run Complete: {folder_name}")
    print(f"View findings: {output_dir.absolute()}/README.md")

if __name__ == "__main__":
    main()
