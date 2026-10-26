"""
mir_engine — Core Audio DSP & MIR Feature Extractor
"""

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

from .extractor import (
    extract_features,
    build_result,
    validate_file,
    compute_rhythmic_complexity,
    compute_syncopation,
    compute_pulse_clarity,
    compute_log_drum_signature,
    compute_danceability_custom,
)

__all__ = [
    "FEATURE_COLUMNS",
    "extract_features",
    "build_result",
    "validate_file",
    "compute_rhythmic_complexity",
    "compute_syncopation",
    "compute_pulse_clarity",
    "compute_log_drum_signature",
    "compute_danceability_custom",
]
