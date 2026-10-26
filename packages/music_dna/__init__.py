"""
Music DNA — Album Playlist Curator
Built on top of diaspora-mir-engine's culturally-informed audio features.

Provides intelligent playlist generation by finding musical connections
and similarities between albums and tracks.
"""

__version__ = "0.1.0"

# Feature vector column order — used consistently across the module
FEATURE_COLUMNS = [
    "bpm",
    "energy_rms",
    "onset_rate",
    "rhythmic_complexity",
    "syncopation",
    "pulse_clarity",
    "log_drum_presence",
    "danceability_custom",
]
