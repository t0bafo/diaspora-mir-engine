"""
Music DNA — Album Playlist Curator
Built on top of diaspora-mir-engine's culturally-informed audio features.

Provides intelligent playlist generation by finding musical connections
and similarities between albums and tracks.
"""

__version__ = "0.1.0"

# mir_engine owns FEATURE_COLUMNS; music_dna re-exports it
from mir_engine import FEATURE_COLUMNS

__all__ = ["FEATURE_COLUMNS", "__version__"]
