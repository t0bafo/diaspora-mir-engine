VISUALS

Every chart, graph, and visualization generated during the MIR project, with guidance on what each shows, why it matters, and where it belongs in the story.

---

1. Syncopation vs. Complexity Scatter Plot
File: full_dataset_v1/syncopation_vs_complexity.png (also: amapiano_corpus/analysis_v1_3/syncopation_vs_complexity.png)
What it shows: Each track plotted by its syncopation score (x-axis) against its rhythmic complexity score (y-axis). Reveals whether complex rhythms correlate with heavy off-beat grooves.
Why it matters: This is the visual that explains why complexity had to be removed from the danceability formula — it shows that African genres cluster in a high-complexity zone that would be penalized by standard Western algorithms.
Best placement: Paragraph 2, alongside the explanation of the v1.2.1 formula decision.

2. Danceability Comparison Bar Chart
File: full_dataset_v1/danceability_comparison.png (also: amapiano_corpus/analysis_v1_3/danceability_comparison.png)
What it shows: Mean danceability scores compared across genres (Amapiano vs. Afrobeats), calculated using the custom v1.2.1 formula.
Why it matters: Demonstrates the practical output of the corrected formula — that Amapiano scores higher than Afrobeats in danceability when the penalty for complexity is removed.
Best placement: Paragraph 3, alongside the 316-track findings and the Kelvin Momo/Shallipopi data points.

3. Pulse Clarity Distribution
File: full_dataset_v1/pulse_clarity_dist.png (also: amapiano_corpus/analysis_v1_3/pulse_clarity_dist.png)
What it shows: Distribution curves of pulse clarity across genres. Amapiano clusters tightly around 0.7–0.85, while Afrobeats is more dispersed around 0.5–0.7.
Why it matters: Visually proves the "house backbone" thesis — that Amapiano carries a consistently stronger internal pulse than Afrobeats despite sounding more rhythmically complex on the surface.
Best placement: Paragraph 3, as a companion to the pulse clarity numbers (0.738 vs. 0.605).

4. K-Means Cluster Scatter (Unsupervised — No Genre Labels)
File: merged_dataset/visuals/cluster_scatter_kmeans.png
What it shows: All 316 tracks plotted on a Syncopation (x) vs. Pulse Clarity (y) grid, colored ONLY by the cluster the machine assigned — Cluster 0, 1, or 2. No human labels were provided.
Why it matters: This is the blind test. The machine found three distinct groupings using math alone. The reader can see the physical separation between the clusters — the "islands" of rhythm.
Best placement: Paragraph 4, as the primary illustration of the unsupervised clustering result.

5. Genre Cluster Scatter (Ground Truth — Human Labels)
File: merged_dataset/visuals/cluster_scatter_genre.png
What it shows: The same 316 tracks on the same axes, but now colored by the human-assigned genre labels (Amapiano, Afrobeats, Afropiano).
Why it matters: When placed side-by-side with visual #4, the reader can see that the machine's blind clusters match the human labels almost exactly. This is the proof that genre is structural, not just cultural.
Best placement: Paragraph 4, directly alongside or immediately after the K-Means scatter. The side-by-side comparison is the visual argument.

6. Full Dataset Cluster Scatter (157-track subset)
File: full_dataset_v1/deep_analysis/cluster_scatter.png
What it shows: An earlier version of the clustering analysis on the initial 157-track Afrobeats-only dataset, showing three natural rhythmic states before the Amapiano corpus was added.
Why it matters: Provides historical context — shows the project evolved from a single-genre analysis to a cross-genre comparison.
Best placement: Not essential for the story, but could serve as a "before" image if the piece discusses the project's evolution.

---

THE SINGLE MOST IMPORTANT VISUAL

If a reader saw nothing else: the side-by-side pairing of cluster_scatter_kmeans.png and cluster_scatter_genre.png.

Individually, the strongest single image is cluster_scatter_kmeans.png — the unsupervised K-Means scatter. It shows three distinct color-coded islands of dots representing 316 songs, grouped by a machine that was never told what genre any of them belonged to. The physical separation between the clusters IS the finding. A reader who looks at that image understands immediately: these genres are mathematically different, and any system that treats them as interchangeable is getting the music wrong.

If only one image can be used, use cluster_scatter_kmeans.png with a caption that reads something like: "316 Afrobeats and Amapiano tracks, clustered by a machine that was never told which was which. It found the difference anyway."
