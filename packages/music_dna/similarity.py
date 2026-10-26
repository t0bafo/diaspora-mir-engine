"""
similarity.py — Cosine similarity engine for Music DNA.

Computes pairwise similarity between tracks using their 8-dimensional
feature vectors. Supports track-to-library search, album centroid
comparison, cross-album mixing, and artist-scoped filtering.
"""

import logging
from typing import Optional

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

from . import FEATURE_COLUMNS
from .database import MusicDNADatabase

log = logging.getLogger(__name__)


class SimilarityEngine:
    """
    Finds sonically similar tracks using cosine similarity on normalized
    audio feature vectors extracted by diaspora-mir-engine.
    """

    def __init__(self, db: MusicDNADatabase):
        self.db = db
        self._scaler: Optional[StandardScaler] = None
        self._fit_ids: Optional[list[int]] = None
        self._fit_matrix: Optional[np.ndarray] = None

    def _ensure_fitted(self):
        """Fit the scaler on the full library if not already done."""
        if self._scaler is not None:
            return
        ids, matrix = self.db.get_feature_matrix()
        if len(ids) == 0:
            raise ValueError("No tracks with features in the database. Run 'ingest' first.")
        self._scaler = StandardScaler()
        self._fit_matrix = self._scaler.fit_transform(matrix)
        self._fit_ids = ids

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors using the library-fitted scaler."""
        self._ensure_fitted()
        return self._scaler.transform(vectors)

    def _get_track_vector(self, track_id: int) -> np.ndarray:
        """Get the raw feature vector for a single track."""
        ids, matrix = self.db.get_feature_matrix(track_ids=[track_id])
        if len(ids) == 0:
            raise ValueError(f"Track {track_id} has no features.")
        return matrix[0]

    def invalidate_cache(self):
        """Clear the fitted scaler (call after adding new tracks)."""
        self._scaler = None
        self._fit_ids = None
        self._fit_matrix = None

    # ── Core Similarity ───────────────────────────────────────────────────────

    def track_similarity(self, track_a_id: int, track_b_id: int) -> float:
        """Compute similarity between two specific tracks. Returns 0.0–1.0."""
        self._ensure_fitted()
        vec_a = self._normalize(self._get_track_vector(track_a_id).reshape(1, -1))
        vec_b = self._normalize(self._get_track_vector(track_b_id).reshape(1, -1))
        return float(cosine_similarity(vec_a, vec_b)[0, 0])

    def album_centroid(self, album_id: int) -> np.ndarray:
        """Compute the mean feature vector (centroid) for an album."""
        tracks = self.db.get_tracks_by_album(album_id)
        if not tracks:
            raise ValueError(f"No tracks found for album {album_id}.")
        ids = [t["id"] for t in tracks]
        track_ids, matrix = self.db.get_feature_matrix(track_ids=ids)
        if len(track_ids) == 0:
            raise ValueError(f"No analyzable tracks in album {album_id}.")
        return matrix.mean(axis=0)

    # ── Search Modes ──────────────────────────────────────────────────────────

    def find_similar_tracks(
        self,
        seed_track_id: int,
        limit: int = 20,
        artist_filter: Optional[str] = None,
        bpm_tolerance: Optional[float] = None,
    ) -> list[tuple[dict, float]]:
        """
        Find the most similar tracks to a seed track.

        Args:
            seed_track_id: The reference track ID.
            limit: Max results to return.
            artist_filter: If set, only search within this artist's catalog.
            bpm_tolerance: If set, exclude tracks with BPM difference > this value.

        Returns:
            List of (track_dict, similarity_score) sorted by descending similarity.
        """
        self._ensure_fitted()
        seed_vec = self._normalize(self._get_track_vector(seed_track_id).reshape(1, -1))

        # Determine which tracks to search against
        artist_id = None
        if artist_filter:
            artists = self.db.search_artists(artist_filter)
            if artists:
                artist_id = artists[0]["id"]

        search_ids, search_matrix = self.db.get_feature_matrix(
            artist_id=artist_id, exclude_track_ids=[seed_track_id]
        )
        if len(search_ids) == 0:
            return []

        search_norm = self._normalize(search_matrix)
        scores = cosine_similarity(seed_vec, search_norm)[0]

        # BPM filtering
        if bpm_tolerance is not None:
            seed_bpm = self._get_track_vector(seed_track_id)[0]  # BPM is first feature
            bpm_col = FEATURE_COLUMNS.index("bpm")
            for i, sid in enumerate(search_ids):
                track_bpm = search_matrix[i, bpm_col]
                if abs(track_bpm - seed_bpm) > bpm_tolerance:
                    scores[i] = -1.0  # Effectively exclude

        # Rank and return
        ranked_indices = np.argsort(scores)[::-1][:limit]
        results = []
        for idx in ranked_indices:
            if scores[idx] < 0:
                continue
            track = self.db.get_track(search_ids[idx])
            results.append((track, float(scores[idx])))
        return results

    def find_similar_to_album(
        self,
        album_id: int,
        limit: int = 20,
        artist_filter: Optional[str] = None,
        bpm_tolerance: Optional[float] = None,
    ) -> list[tuple[dict, float]]:
        """
        Find tracks similar to an album's overall vibe (centroid).

        Args:
            album_id: The reference album ID.
            limit: Max results.
            artist_filter: Restrict search to this artist.
            bpm_tolerance: Max BPM difference from album's average BPM.

        Returns:
            List of (track_dict, similarity_score) sorted descending.
        """
        self._ensure_fitted()
        centroid = self.album_centroid(album_id)
        centroid_norm = self._normalize(centroid.reshape(1, -1))

        # Exclude tracks that are ON the reference album
        album_tracks = self.db.get_tracks_by_album(album_id)
        exclude_ids = [t["id"] for t in album_tracks]

        artist_id = None
        if artist_filter:
            artists = self.db.search_artists(artist_filter)
            if artists:
                artist_id = artists[0]["id"]

        search_ids, search_matrix = self.db.get_feature_matrix(
            artist_id=artist_id, exclude_track_ids=exclude_ids
        )
        if len(search_ids) == 0:
            return []

        search_norm = self._normalize(search_matrix)
        scores = cosine_similarity(centroid_norm, search_norm)[0]

        # BPM filtering
        if bpm_tolerance is not None:
            avg_bpm = centroid[FEATURE_COLUMNS.index("bpm")]
            bpm_col = FEATURE_COLUMNS.index("bpm")
            for i in range(len(search_ids)):
                if abs(search_matrix[i, bpm_col] - avg_bpm) > bpm_tolerance:
                    scores[i] = -1.0

        ranked_indices = np.argsort(scores)[::-1][:limit]
        results = []
        for idx in ranked_indices:
            if scores[idx] < 0:
                continue
            track = self.db.get_track(search_ids[idx])
            results.append((track, float(scores[idx])))
        return results

    def mix_albums(
        self,
        album_a_id: int,
        album_b_id: int,
        limit: int = 30,
    ) -> list[tuple[dict, float, str]]:
        """
        Create a cross-album mix by finding the best pairwise matches
        between two albums and interleaving them.

        Returns:
            List of (track_dict, similarity_score, source_label) where
            source_label indicates which album the track came from.
        """
        self._ensure_fitted()

        album_a = self.db.get_album(album_a_id)
        album_b = self.db.get_album(album_b_id)
        if not album_a or not album_b:
            raise ValueError("One or both albums not found.")

        tracks_a = self.db.get_tracks_by_album(album_a_id)
        tracks_b = self.db.get_tracks_by_album(album_b_id)
        if not tracks_a or not tracks_b:
            raise ValueError("One or both albums have no tracks.")

        ids_a = [t["id"] for t in tracks_a]
        ids_b = [t["id"] for t in tracks_b]

        # Get feature matrices for both albums
        _, matrix_a = self.db.get_feature_matrix(track_ids=ids_a)
        _, matrix_b = self.db.get_feature_matrix(track_ids=ids_b)

        norm_a = self._normalize(matrix_a)
        norm_b = self._normalize(matrix_b)

        # Compute cross-album similarity matrix
        cross_sim = cosine_similarity(norm_a, norm_b)  # shape: (len_a, len_b)

        # Build interleaved playlist using greedy best-match pairing
        label_a = album_a["title"]
        label_b = album_b["title"]
        playlist: list[tuple[dict, float, str]] = []
        used_a = set()
        used_b = set()

        # Flatten cross_sim into (score, idx_a, idx_b) and sort descending
        pairs = []
        for i in range(len(ids_a)):
            for j in range(len(ids_b)):
                pairs.append((cross_sim[i, j], i, j))
        pairs.sort(key=lambda x: x[0], reverse=True)

        for score, idx_a, idx_b in pairs:
            if idx_a in used_a and idx_b in used_b:
                continue
            if len(playlist) >= limit:
                break

            # Add track from A if not yet used
            if idx_a not in used_a:
                track_a = self.db.get_track(ids_a[idx_a])
                playlist.append((track_a, float(score), label_a))
                used_a.add(idx_a)

            # Add its best match from B if not yet used
            if idx_b not in used_b and len(playlist) < limit:
                track_b = self.db.get_track(ids_b[idx_b])
                playlist.append((track_b, float(score), label_b))
                used_b.add(idx_b)

        # Add any remaining unpaired tracks from either album
        for i, tid in enumerate(ids_a):
            if i not in used_a and len(playlist) < limit:
                track = self.db.get_track(tid)
                playlist.append((track, 0.0, label_a))
        for j, tid in enumerate(ids_b):
            if j not in used_b and len(playlist) < limit:
                track = self.db.get_track(tid)
                playlist.append((track, 0.0, label_b))

        return playlist
