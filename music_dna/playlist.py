"""
playlist.py — Playlist generation and export for Music DNA.

Takes similarity results and sequences them into playable playlists
with optional BPM smoothing and energy arc shaping.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class PlaylistEntry:
    """A single entry in a playlist."""
    track: dict
    score: float  # Similarity score (0.0–1.0)
    source: str = ""  # e.g., album name or "Similar to X"

    @property
    def artist(self) -> str:
        return self.track.get("artist_name") or "Unknown"

    @property
    def title(self) -> str:
        return self.track.get("title") or "Unknown"

    @property
    def bpm(self) -> float:
        return self.track.get("bpm") or 0.0

    @property
    def energy(self) -> float:
        return self.track.get("energy_rms") or 0.0

    @property
    def file_path(self) -> Optional[str]:
        return self.track.get("file_path")


@dataclass
class Playlist:
    """An ordered collection of tracks with export capabilities."""
    name: str
    entries: list[PlaylistEntry] = field(default_factory=list)
    description: str = ""

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    # ── Sequencing ────────────────────────────────────────────────────────────

    def sequence_by_similarity(self):
        """Order entries by descending similarity score (highest match first)."""
        self.entries.sort(key=lambda e: e.score, reverse=True)

    def sequence_by_bpm(self):
        """Order entries for smooth BPM transitions (nearest-neighbor chain)."""
        if len(self.entries) <= 2:
            return

        # Greedy nearest-neighbor on BPM
        remaining = list(range(len(self.entries)))
        ordered = [remaining.pop(0)]  # Start with first entry

        while remaining:
            last_bpm = self.entries[ordered[-1]].bpm
            # Find the closest BPM in remaining
            best_idx = min(remaining, key=lambda i: abs(self.entries[i].bpm - last_bpm))
            remaining.remove(best_idx)
            ordered.append(best_idx)

        self.entries = [self.entries[i] for i in ordered]

    def sequence_by_energy_arc(self):
        """
        Order entries in an energy arc: build → peak → cool down.

        Splits entries into thirds: ascending energy, peak, descending energy.
        """
        if len(self.entries) <= 3:
            return

        # Sort by energy
        by_energy = sorted(range(len(self.entries)), key=lambda i: self.entries[i].energy)

        n = len(by_energy)
        third = n // 3

        # Build-up: low to medium energy
        buildup = by_energy[:third]
        # Peak: highest energy
        peak = by_energy[third:2*third]
        peak.reverse()  # Keep peak energy high
        # Cool-down: medium back to low
        cooldown = by_energy[2*third:]
        cooldown.reverse()

        arc_order = buildup + peak + cooldown
        self.entries = [self.entries[i] for i in arc_order]

    # ── Interleave sequencing (for mix mode) ──────────────────────────────────

    def sequence_interleaved(self):
        """
        Interleave entries by source label (for cross-album mixes).
        Alternates between sources while maintaining relative order.
        """
        sources = {}
        for entry in self.entries:
            sources.setdefault(entry.source, []).append(entry)

        if len(sources) < 2:
            return  # Nothing to interleave

        # Get the two source lists
        source_lists = list(sources.values())
        interleaved = []
        i, j = 0, 0
        while i < len(source_lists[0]) or j < len(source_lists[1]):
            if i < len(source_lists[0]):
                interleaved.append(source_lists[0][i])
                i += 1
            if j < len(source_lists[1]):
                interleaved.append(source_lists[1][j])
                j += 1

        self.entries = interleaved

    # ── Export ────────────────────────────────────────────────────────────────

    def export_m3u(self, output_path: str):
        """Export playlist as M3U file (playable in VLC, Foobar2000, etc.)."""
        path = Path(output_path)
        lines = ["#EXTM3U", f"#PLAYLIST:{self.name}"]

        for entry in self.entries:
            if entry.file_path:
                duration = int(entry.track.get("duration_seconds") or -1)
                lines.append(f"#EXTINF:{duration},{entry.artist} - {entry.title}")
                lines.append(entry.file_path)

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log.info(f"Exported M3U playlist to {path}")

    def export_json(self, output_path: str):
        """Export playlist as JSON."""
        data = {
            "name": self.name,
            "description": self.description,
            "track_count": len(self.entries),
            "tracks": [
                {
                    "position": i + 1,
                    "artist": e.artist,
                    "title": e.title,
                    "album": e.track.get("album_title") or "",
                    "bpm": e.bpm,
                    "similarity_score": round(e.score, 4),
                    "source": e.source,
                    "genre": e.track.get("genre") or "",
                    "file_path": e.file_path,
                }
                for i, e in enumerate(self.entries)
            ],
        }
        Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        log.info(f"Exported JSON playlist to {output_path}")

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self, show_scores: bool = True) -> str:
        """
        Format the playlist for terminal display.

        Returns a formatted string with track listing.
        """
        lines = []
        lines.append("")
        lines.append(f"  🧬 {self.name}")
        if self.description:
            lines.append(f"  {self.description}")
        lines.append(f"  ─── {len(self.entries)} tracks ───")
        lines.append("")

        # Column headers
        if show_scores:
            lines.append(f"  {'#':>3}  {'Score':>6}  {'Artist':<25} {'Title':<30} {'BPM':>5}  {'Source'}")
            lines.append(f"  {'─'*3}  {'─'*6}  {'─'*25} {'─'*30} {'─'*5}  {'─'*15}")
        else:
            lines.append(f"  {'#':>3}  {'Artist':<25} {'Title':<30} {'BPM':>5}  {'Source'}")
            lines.append(f"  {'─'*3}  {'─'*25} {'─'*30} {'─'*5}  {'─'*15}")

        for i, entry in enumerate(self.entries, 1):
            artist = (entry.artist[:23] + "..") if len(entry.artist) > 25 else entry.artist
            title = (entry.title[:28] + "..") if len(entry.title) > 30 else entry.title
            bpm = f"{entry.bpm:.0f}" if entry.bpm else "  –"
            source = entry.source[:15] if entry.source else ""

            if show_scores:
                score_str = f"{entry.score:.3f}" if entry.score > 0 else "  –  "
                lines.append(f"  {i:>3}  {score_str:>6}  {artist:<25} {title:<30} {bpm:>5}  {source}")
            else:
                lines.append(f"  {i:>3}  {artist:<25} {title:<30} {bpm:>5}  {source}")

        lines.append("")
        return "\n".join(lines)


# ── Playlist builders (convenience functions) ─────────────────────────────────

def build_from_similar(
    results: list[tuple[dict, float]],
    name: str,
    description: str = "",
) -> Playlist:
    """Build a playlist from similarity search results."""
    entries = [
        PlaylistEntry(track=track, score=score, source="Similar")
        for track, score in results
    ]
    return Playlist(name=name, entries=entries, description=description)


def build_from_mix(
    results: list[tuple[dict, float, str]],
    name: str,
    description: str = "",
) -> Playlist:
    """Build a playlist from cross-album mix results."""
    entries = [
        PlaylistEntry(track=track, score=score, source=source)
        for track, score, source in results
    ]
    return Playlist(name=name, entries=entries, description=description)
