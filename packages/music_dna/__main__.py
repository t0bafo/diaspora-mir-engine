"""
__main__.py — CLI entry point for Music DNA.

Run with:
    python -m music_dna <command> [args]

Commands:
    ingest          Scan a directory and analyze audio files
    import-corpus   Import existing feature data (JSON or CSV)
    similar         Find tracks similar to an album
    discover        Library-wide similarity search
    mix             Cross-album playlist mix
    list            List artists, albums, or tracks in the database
    info            Show database statistics
"""

import argparse
import logging
import sys
from pathlib import Path

from .config import MUSIC_DNA_CORPUS_PATH
from .database import MusicDNADatabase, DEFAULT_DB_PATH
from .ingest import ingest_directory, import_corpus_json, import_corpus_csv
from .similarity import SimilarityEngine
from .playlist import build_from_similar, build_from_mix

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_album(db: MusicDNADatabase, query: str, artist_hint: str = None) -> dict:
    """
    Resolve an album query string to a single album record.
    Raises SystemExit with helpful message if ambiguous or not found.
    """
    matches = db.search_albums(query)

    if artist_hint:
        # Filter by artist if provided
        filtered = [m for m in matches if artist_hint.lower() in m.get("artist_name", "").lower()]
        if filtered:
            matches = filtered

    if not matches:
        print(f"\n  ❌ No album found matching '{query}'")
        print("  Run 'python -m music_dna list albums' to see available albums.\n")
        sys.exit(1)

    if len(matches) == 1:
        return matches[0]

    # Ambiguous — show options
    print(f"\n  Multiple albums match '{query}':")
    for i, m in enumerate(matches, 1):
        print(f"    {i}. {m['artist_name']} — {m['title']}")
    try:
        choice = int(input("\n  Enter number: ")) - 1
        if 0 <= choice < len(matches):
            return matches[choice]
    except (ValueError, EOFError):
        pass
    print("  Invalid selection.")
    sys.exit(1)


def _resolve_artist_id(db: MusicDNADatabase, query: str) -> int:
    """Resolve an artist query to an artist ID."""
    matches = db.search_artists(query)
    if not matches:
        print(f"\n  ❌ No artist found matching '{query}'")
        sys.exit(1)
    if len(matches) == 1:
        return matches[0]["id"]

    print(f"\n  Multiple artists match '{query}':")
    for i, m in enumerate(matches, 1):
        print(f"    {i}. {m['name']}")
    try:
        choice = int(input("\n  Enter number: ")) - 1
        if 0 <= choice < len(matches):
            return matches[choice]["id"]
    except (ValueError, EOFError):
        pass
    print("  Invalid selection.")
    sys.exit(1)


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_ingest(args):
    """Scan a directory and analyze audio files."""
    db = MusicDNADatabase(args.db)
    stats = ingest_directory(args.directory, db, default_genre=args.genre)
    db.close()

    print(f"\n  ✅ Ingestion complete:")
    print(f"     Analyzed:  {stats['processed']}")
    print(f"     Skipped:   {stats['skipped']}")
    print(f"     Failed:    {stats['failed']}\n")


def cmd_import(args):
    """Import an existing feature corpus (JSON or CSV)."""
    db = MusicDNADatabase(args.db)

    path = Path(args.file)
    if path.suffix.lower() == ".json":
        stats = import_corpus_json(args.file, db)
        print(f"\n  ✅ JSON import complete: {stats['imported']} tracks imported, {stats['skipped']} skipped.\n")
    elif path.suffix.lower() == ".csv":
        stats = import_corpus_csv(args.file, db)
        print(f"\n  ✅ CSV import complete: {stats['imported']} tracks imported, {stats['skipped']} skipped.\n")
    else:
        print(f"\n  ❌ Unsupported format: {path.suffix}. Use .json or .csv.\n")
        sys.exit(1)

    db.close()


def cmd_similar(args):
    """Find tracks similar to an album."""
    db = MusicDNADatabase(args.db)
    engine = SimilarityEngine(db)

    album = _resolve_album(db, args.album, artist_hint=args.artist)
    print(f"\n  🔍 Finding tracks similar to: {album['artist_name']} — {album['title']}")

    results = engine.find_similar_to_album(
        album["id"],
        limit=args.limit,
        artist_filter=args.artist,
        bpm_tolerance=args.bpm_tolerance,
    )

    if not results:
        print("  No similar tracks found.\n")
        db.close()
        return

    description = f"Tracks similar to {album['artist_name']} — {album['title']}"
    if args.artist:
        description += f" (filtered to {args.artist})"

    playlist = build_from_similar(results, name=f"Similar to {album['title']}", description=description)

    if args.sequence == "bpm":
        playlist.sequence_by_bpm()
    elif args.sequence == "energy":
        playlist.sequence_by_energy_arc()
    else:
        playlist.sequence_by_similarity()

    print(playlist.display())

    if args.output:
        if args.output.endswith(".m3u"):
            playlist.export_m3u(args.output)
        elif args.output.endswith(".json"):
            playlist.export_json(args.output)
        else:
            playlist.export_json(args.output + ".json")
        print(f"  📁 Exported to: {args.output}\n")

    db.close()


def cmd_discover(args):
    """Library-wide discovery — find everything similar to an album."""
    db = MusicDNADatabase(args.db)
    engine = SimilarityEngine(db)

    album = _resolve_album(db, args.album)
    print(f"\n  🔍 Discovering tracks similar to: {album['artist_name']} — {album['title']}")

    results = engine.find_similar_to_album(
        album["id"],
        limit=args.limit,
        bpm_tolerance=args.bpm_tolerance,
    )

    if not results:
        print("  No similar tracks found.\n")
        db.close()
        return

    playlist = build_from_similar(
        results,
        name=f"Discover: {album['title']}",
        description=f"Everything in your library that sounds like {album['artist_name']} — {album['title']}",
    )

    if args.sequence == "bpm":
        playlist.sequence_by_bpm()
    elif args.sequence == "energy":
        playlist.sequence_by_energy_arc()
    else:
        playlist.sequence_by_similarity()

    print(playlist.display())

    if args.output:
        if args.output.endswith(".m3u"):
            playlist.export_m3u(args.output)
        elif args.output.endswith(".json"):
            playlist.export_json(args.output)
        else:
            playlist.export_json(args.output + ".json")
        print(f"  📁 Exported to: {args.output}\n")

    db.close()


def cmd_mix(args):
    """Cross-album mix — blend two albums together."""
    db = MusicDNADatabase(args.db)
    engine = SimilarityEngine(db)

    album_a = _resolve_album(db, args.album_a)
    album_b = _resolve_album(db, args.album_b)

    print(f"\n  🎛️  Mixing:")
    print(f"     Album A: {album_a['artist_name']} — {album_a['title']}")
    print(f"     Album B: {album_b['artist_name']} — {album_b['title']}")

    results = engine.mix_albums(album_a["id"], album_b["id"], limit=args.limit)

    if not results:
        print("  Could not generate mix.\n")
        db.close()
        return

    playlist = build_from_mix(
        results,
        name=f"{album_a['title']} × {album_b['title']}",
        description=f"Cross-album mix of {album_a['artist_name']} and {album_b['artist_name']}",
    )

    if args.sequence == "bpm":
        playlist.sequence_by_bpm()
    elif args.sequence == "energy":
        playlist.sequence_by_energy_arc()
    elif args.sequence == "interleave":
        playlist.sequence_interleaved()
    # default: keep the mix order from the engine

    print(playlist.display())

    if args.output:
        if args.output.endswith(".m3u"):
            playlist.export_m3u(args.output)
        elif args.output.endswith(".json"):
            playlist.export_json(args.output)
        else:
            playlist.export_json(args.output + ".json")
        print(f"  📁 Exported to: {args.output}\n")

    db.close()


def cmd_list(args):
    """List entities in the database."""
    db = MusicDNADatabase(args.db)

    if args.entity == "artists":
        artists = db.list_artists()
        if not artists:
            print("\n  No artists in the database.\n")
        else:
            print(f"\n  {'Artist':<30} {'Tracks':>7} {'Albums':>7}")
            print(f"  {'─'*30} {'─'*7} {'─'*7}")
            for a in artists:
                print(f"  {a['name']:<30} {a['track_count']:>7} {a['album_count']:>7}")
            print()

    elif args.entity == "albums":
        albums = db.list_albums()
        if not albums:
            print("\n  No albums in the database.\n")
        else:
            print(f"\n  {'Artist':<25} {'Album':<30} {'Tracks':>7}")
            print(f"  {'─'*25} {'─'*30} {'─'*7}")
            for a in albums:
                artist = (a['artist_name'][:23] + "..") if len(a['artist_name']) > 25 else a['artist_name']
                title = (a['title'][:28] + "..") if len(a['title']) > 30 else a['title']
                print(f"  {artist:<25} {title:<30} {a['track_count']:>7}")
            print()

    elif args.entity == "tracks":
        tracks = db.get_all_tracks()
        if not tracks:
            print("\n  No tracks in the database.\n")
        else:
            print(f"\n  {'Artist':<25} {'Title':<30} {'BPM':>5} {'Dance':>6} {'Genre':<12}")
            print(f"  {'─'*25} {'─'*30} {'─'*5} {'─'*6} {'─'*12}")
            for t in tracks[:100]:  # Limit display to 100
                artist = ((t.get('artist_name') or 'Unknown')[:23] + "..") if len(t.get('artist_name') or '') > 25 else (t.get('artist_name') or 'Unknown')
                title = (t['title'][:28] + "..") if len(t['title']) > 30 else t['title']
                bpm = f"{t['bpm']:.0f}" if t.get('bpm') else "  –"
                dance = f"{t['danceability_custom']:.3f}" if t.get('danceability_custom') else "  –  "
                genre = (t.get('genre') or '')[:12]
                print(f"  {artist:<25} {title:<30} {bpm:>5} {dance:>6} {genre:<12}")
            if len(tracks) > 100:
                print(f"\n  ... and {len(tracks) - 100} more tracks")
            print()

    db.close()


def cmd_info(args):
    """Show database statistics."""
    db = MusicDNADatabase(args.db)
    stats = db.get_stats()
    db.close()

    print(f"\n  🧬 Music DNA Database: {args.db}")
    print(f"  ─────────────────────────────")
    print(f"  Artists:  {stats['artists']}")
    print(f"  Albums:   {stats['albums']}")
    print(f"  Tracks:   {stats['tracks']}")
    print(f"  Genres:   {', '.join(stats['genres']) if stats['genres'] else '–'}")
    print()


# ── Argument Parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="music-dna",
        description="🧬 Music DNA — Album Playlist Curator powered by diaspora-mir-engine",
    )
    parser.add_argument(
        "--db", default=str(DEFAULT_DB_PATH),
        help=f"Path to the SQLite database (default: {DEFAULT_DB_PATH})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── ingest ────────────────────────────────────────────────────────────────
    p_ingest = subparsers.add_parser("ingest", help="Scan and analyze audio files")
    p_ingest.add_argument("directory", help="Directory to scan (artist/album/track structure)")
    p_ingest.add_argument("--genre", help="Default genre label for all tracks")
    p_ingest.set_defaults(func=cmd_ingest)

    # ── import-corpus ─────────────────────────────────────────────────────────
    p_import = subparsers.add_parser("import-corpus", help="Import existing feature data")
    p_import.add_argument("file", nargs="?", default=str(MUSIC_DNA_CORPUS_PATH), help=f"JSON or CSV feature file (default: {MUSIC_DNA_CORPUS_PATH.name})")
    p_import.set_defaults(func=cmd_import)

    # ── similar ───────────────────────────────────────────────────────────────
    p_similar = subparsers.add_parser("similar", help="Find tracks similar to an album")
    p_similar.add_argument("album", help="Album name to search for")
    p_similar.add_argument("--artist", help="Filter results to this artist's catalog")
    p_similar.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    p_similar.add_argument("--bpm-tolerance", type=float, help="Max BPM difference from reference")
    p_similar.add_argument("--sequence", choices=["similarity", "bpm", "energy"], default="similarity",
                           help="Playlist ordering strategy (default: similarity)")
    p_similar.add_argument("--output", "-o", help="Export playlist to file (.m3u or .json)")
    p_similar.set_defaults(func=cmd_similar)

    # ── discover ──────────────────────────────────────────────────────────────
    p_discover = subparsers.add_parser("discover", help="Library-wide similarity search")
    p_discover.add_argument("album", help="Album name to use as reference")
    p_discover.add_argument("--limit", type=int, default=30, help="Max results (default: 30)")
    p_discover.add_argument("--bpm-tolerance", type=float, help="Max BPM difference from reference")
    p_discover.add_argument("--sequence", choices=["similarity", "bpm", "energy"], default="similarity",
                            help="Playlist ordering strategy (default: similarity)")
    p_discover.add_argument("--output", "-o", help="Export playlist to file (.m3u or .json)")
    p_discover.set_defaults(func=cmd_discover)

    # ── mix ───────────────────────────────────────────────────────────────────
    p_mix = subparsers.add_parser("mix", help="Cross-album playlist mix")
    p_mix.add_argument("album_a", help="First album name")
    p_mix.add_argument("album_b", help="Second album name")
    p_mix.add_argument("--limit", type=int, default=30, help="Max tracks (default: 30)")
    p_mix.add_argument("--sequence", choices=["match", "bpm", "energy", "interleave"], default="match",
                       help="Sequencing strategy (default: match)")
    p_mix.add_argument("--output", "-o", help="Export playlist to file (.m3u or .json)")
    p_mix.set_defaults(func=cmd_mix)

    # ── list ──────────────────────────────────────────────────────────────────
    p_list = subparsers.add_parser("list", help="List artists, albums, or tracks")
    p_list.add_argument("entity", choices=["artists", "albums", "tracks"],
                        help="What to list")
    p_list.set_defaults(func=cmd_list)

    # ── info ──────────────────────────────────────────────────────────────────
    p_info = subparsers.add_parser("info", help="Show database statistics")
    p_info.set_defaults(func=cmd_info)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
