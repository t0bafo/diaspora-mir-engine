"""
database.py — SQLite storage layer for Music DNA.

Stores track metadata, audio features, and album/artist relationships.
Provides queryable access to the feature vectors used by the similarity engine.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

import numpy as np

from . import FEATURE_COLUMNS

log = logging.getLogger(__name__)

# ── Default database path ─────────────────────────────────────────────────────
DEFAULT_DB_PATH = Path(__file__).parent.parent / "music_dna.db"

# ── Schema ─────────────────────────────────────────────────────────────────────
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE,
    UNIQUE(name COLLATE NOCASE)
);

CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL COLLATE NOCASE,
    artist_id INTEGER REFERENCES artists(id),
    UNIQUE(title COLLATE NOCASE, artist_id)
);

CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_path TEXT,
    album_id INTEGER REFERENCES albums(id),
    artist_id INTEGER REFERENCES artists(id),
    genre TEXT,
    -- 8-dimensional feature vector
    bpm REAL,
    energy_rms REAL,
    onset_rate REAL,
    rhythmic_complexity REAL,
    syncopation REAL,
    pulse_clarity REAL,
    log_drum_presence REAL,
    danceability_custom REAL,
    -- Additional metadata
    duration_seconds REAL,
    backend TEXT,
    analyzed_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist_id);
CREATE INDEX IF NOT EXISTS idx_tracks_album ON tracks(album_id);
CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre);
"""


class MusicDNADatabase:
    """SQLite-backed storage for Music DNA track features and metadata."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript(_SCHEMA_SQL)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ── Artists ────────────────────────────────────────────────────────────────

    def add_artist(self, name: str) -> int:
        """Insert or retrieve an artist. Returns the artist ID."""
        name = name.strip()
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO artists (name) VALUES (?)", (name,)
        )
        if cur.rowcount > 0:
            self.conn.commit()
            return cur.lastrowid
        # Already existed — look it up
        row = self.conn.execute(
            "SELECT id FROM artists WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        return row["id"]

    def get_artist(self, artist_id: int) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM artists WHERE id = ?", (artist_id,)
        ).fetchone()
        return dict(row) if row else None

    def search_artists(self, query: str) -> list[dict]:
        """Fuzzy search artists by name (case-insensitive LIKE)."""
        rows = self.conn.execute(
            "SELECT * FROM artists WHERE name LIKE ? COLLATE NOCASE",
            (f"%{query}%",),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Albums ────────────────────────────────────────────────────────────────

    def add_album(self, title: str, artist_id: int) -> int:
        """Insert or retrieve an album. Returns the album ID."""
        title = title.strip()
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO albums (title, artist_id) VALUES (?, ?)",
            (title, artist_id),
        )
        if cur.rowcount > 0:
            self.conn.commit()
            return cur.lastrowid
        row = self.conn.execute(
            "SELECT id FROM albums WHERE title = ? COLLATE NOCASE AND artist_id = ?",
            (title, artist_id),
        ).fetchone()
        return row["id"]

    def get_album(self, album_id: int) -> Optional[dict]:
        row = self.conn.execute(
            """SELECT a.*, ar.name as artist_name
               FROM albums a JOIN artists ar ON a.artist_id = ar.id
               WHERE a.id = ?""",
            (album_id,),
        ).fetchone()
        return dict(row) if row else None

    def search_albums(self, query: str) -> list[dict]:
        """Fuzzy search albums by title (case-insensitive LIKE)."""
        rows = self.conn.execute(
            """SELECT a.*, ar.name as artist_name
               FROM albums a JOIN artists ar ON a.artist_id = ar.id
               WHERE a.title LIKE ? COLLATE NOCASE""",
            (f"%{query}%",),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Tracks ────────────────────────────────────────────────────────────────

    def add_track(
        self,
        title: str,
        features: dict,
        artist_id: Optional[int] = None,
        album_id: Optional[int] = None,
        file_path: Optional[str] = None,
        genre: Optional[str] = None,
        duration: Optional[float] = None,
        backend: Optional[str] = None,
    ) -> int:
        """Insert a track with its feature vector. Returns the track ID."""
        cur = self.conn.execute(
            """INSERT INTO tracks
               (title, file_path, album_id, artist_id, genre,
                bpm, energy_rms, onset_rate,
                rhythmic_complexity, syncopation, pulse_clarity,
                log_drum_presence, danceability_custom,
                duration_seconds, backend)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                file_path,
                album_id,
                artist_id,
                genre,
                features.get("bpm"),
                features.get("energy_rms"),
                features.get("onset_rate"),
                features.get("rhythmic_complexity"),
                features.get("syncopation"),
                features.get("pulse_clarity"),
                features.get("log_drum_presence"),
                features.get("danceability_custom"),
                duration,
                backend,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def track_exists(self, file_path: str) -> bool:
        """Check if a track with this file path is already in the database."""
        row = self.conn.execute(
            "SELECT 1 FROM tracks WHERE file_path = ?", (file_path,)
        ).fetchone()
        return row is not None

    def track_exists_by_title_artist(self, title: str, artist_id: int) -> bool:
        """Check if a track with this title and artist already exists."""
        row = self.conn.execute(
            "SELECT 1 FROM tracks WHERE title = ? COLLATE NOCASE AND artist_id = ?",
            (title, artist_id),
        ).fetchone()
        return row is not None

    def get_track(self, track_id: int) -> Optional[dict]:
        row = self.conn.execute(
            """SELECT t.*,
                      ar.name as artist_name,
                      al.title as album_title
               FROM tracks t
               LEFT JOIN artists ar ON t.artist_id = ar.id
               LEFT JOIN albums al ON t.album_id = al.id
               WHERE t.id = ?""",
            (track_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_tracks_by_album(self, album_id: int) -> list[dict]:
        rows = self.conn.execute(
            """SELECT t.*, ar.name as artist_name, al.title as album_title
               FROM tracks t
               LEFT JOIN artists ar ON t.artist_id = ar.id
               LEFT JOIN albums al ON t.album_id = al.id
               WHERE t.album_id = ?
               ORDER BY t.title""",
            (album_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_tracks_by_artist(self, artist_id: int) -> list[dict]:
        rows = self.conn.execute(
            """SELECT t.*, ar.name as artist_name, al.title as album_title
               FROM tracks t
               LEFT JOIN artists ar ON t.artist_id = ar.id
               LEFT JOIN albums al ON t.album_id = al.id
               WHERE t.artist_id = ?
               ORDER BY al.title, t.title""",
            (artist_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_tracks(self) -> list[dict]:
        rows = self.conn.execute(
            """SELECT t.*, ar.name as artist_name, al.title as album_title
               FROM tracks t
               LEFT JOIN artists ar ON t.artist_id = ar.id
               LEFT JOIN albums al ON t.album_id = al.id
               ORDER BY ar.name, al.title, t.title"""
        ).fetchall()
        return [dict(r) for r in rows]

    def search_tracks(self, query: str) -> list[dict]:
        """Fuzzy search tracks by title (case-insensitive LIKE)."""
        rows = self.conn.execute(
            """SELECT t.*, ar.name as artist_name, al.title as album_title
               FROM tracks t
               LEFT JOIN artists ar ON t.artist_id = ar.id
               LEFT JOIN albums al ON t.album_id = al.id
               WHERE t.title LIKE ? COLLATE NOCASE""",
            (f"%{query}%",),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Feature Matrix ────────────────────────────────────────────────────────

    def get_feature_matrix(
        self,
        track_ids: Optional[list[int]] = None,
        artist_id: Optional[int] = None,
        exclude_track_ids: Optional[list[int]] = None,
    ) -> tuple[list[int], np.ndarray]:
        """
        Retrieve feature vectors as a NumPy matrix.

        Returns:
            (track_ids, feature_matrix) where feature_matrix is shape (N, 8).
            Rows with any NULL features are excluded.
        """
        cols = ", ".join(FEATURE_COLUMNS)
        query = f"SELECT id, {cols} FROM tracks WHERE 1=1"
        params: list = []

        if track_ids is not None:
            placeholders = ",".join("?" * len(track_ids))
            query += f" AND id IN ({placeholders})"
            params.extend(track_ids)

        if artist_id is not None:
            query += " AND artist_id = ?"
            params.append(artist_id)

        if exclude_track_ids:
            placeholders = ",".join("?" * len(exclude_track_ids))
            query += f" AND id NOT IN ({placeholders})"
            params.extend(exclude_track_ids)

        rows = self.conn.execute(query, params).fetchall()

        ids = []
        vectors = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get("bpm") is None:
                continue
            feature_vals = [
                row_dict[col] if row_dict.get(col) is not None else 0.0
                for col in FEATURE_COLUMNS
            ]
            ids.append(row_dict["id"])
            vectors.append(feature_vals)

        if not vectors:
            return [], np.empty((0, len(FEATURE_COLUMNS)))

        return ids, np.array(vectors, dtype=float)

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return summary statistics about the database."""
        artists = self.conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0]
        albums = self.conn.execute("SELECT COUNT(*) FROM albums").fetchone()[0]
        tracks = self.conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        genres = self.conn.execute(
            "SELECT DISTINCT genre FROM tracks WHERE genre IS NOT NULL"
        ).fetchall()
        return {
            "artists": artists,
            "albums": albums,
            "tracks": tracks,
            "genres": [r[0] for r in genres],
        }

    def list_artists(self) -> list[dict]:
        """List all artists with track counts."""
        rows = self.conn.execute(
            """SELECT ar.id, ar.name,
                      COUNT(t.id) as track_count,
                      COUNT(DISTINCT t.album_id) as album_count
               FROM artists ar
               LEFT JOIN tracks t ON t.artist_id = ar.id
               GROUP BY ar.id
               ORDER BY ar.name"""
        ).fetchall()
        return [dict(r) for r in rows]

    def list_albums(self) -> list[dict]:
        """List all albums with artist name and track counts."""
        rows = self.conn.execute(
            """SELECT al.id, al.title, ar.name as artist_name,
                      COUNT(t.id) as track_count
               FROM albums al
               JOIN artists ar ON al.artist_id = ar.id
               LEFT JOIN tracks t ON t.album_id = al.id
               GROUP BY al.id
               ORDER BY ar.name, al.title"""
        ).fetchall()
        return [dict(r) for r in rows]
