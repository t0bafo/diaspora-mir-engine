"""
analyze_track.py — Music Information Retrieval (MIR) feature extractor v1.2.1

Extracts tempo (BPM), RMS energy, onset rate, and mid-level groove features:
  - Rhythmic Complexity  (IOI coefficient of variation)
  - Syncopation          (16th-note offbeat emphasis)
  - Pulse Clarity        (onset-envelope autocorrelation at beat lag)
  - Log Drum Signature   (sub-bass energy ratio + spectral centroid)
  - Danceability Custom  (v1.3.0 revised: includes log drum weight)

Uses Essentia as primary backend; falls back to librosa.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".aiff", ".m4a"}


# ── Utility ────────────────────────────────────────────────────────────────────

def validate_file(path: str) -> Path:
    """Validate the input file exists and has a supported extension."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    if not p.is_file():
        raise ValueError(f"Path is not a file: {path}")
    if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported format '{p.suffix}'.")
    return p


# ── Groove / Mid-level Features (Pure NumPy) ──────────────────────────────────

def compute_rhythmic_complexity(onset_times) -> float:
    """
    Rhythmic Complexity — variability in inter-onset intervals (IOIs).
    cv = std(ioi) / mean(ioi)
    complexity = tanh(cv * 1.5)
    """
    import numpy as np
    onset_times = np.asarray(onset_times, dtype=float)
    if len(onset_times) < 3:
        return 0.0

    ioi = np.diff(onset_times)
    ioi = ioi[ioi > 0.02]  # ignore very small noise intervals
    if len(ioi) < 2:
        return 0.0

    cv = np.std(ioi) / (np.mean(ioi) + 1e-8)
    complexity = np.tanh(cv * 1.5)
    return round(float(complexity), 4)


def compute_syncopation(onset_times, beat_times) -> float:
    """
    Syncopation — Detection of intentional 16th-note offbeats.
    Checks for onsets at phase ~0.25 and ~0.75 relative to the beat grid.
    Tolerance: ±10% (0.1).
    """
    import numpy as np
    onset_times = np.asarray(onset_times, dtype=float)
    beat_times = np.asarray(beat_times, dtype=float)

    if len(onset_times) < 2 or len(beat_times) < 2:
        return 0.0

    # Calculate median beat period to handle local drift
    beat_period = np.median(np.diff(beat_times))
    if beat_period <= 0:
        return 0.0

    hits = 0
    total = len(onset_times)

    for t in onset_times:
        # Find distance to start of nearest beat
        # Using simple phase relative to the closest beat
        idx = np.argmin(np.abs(beat_times - t))
        nearest_beat = beat_times[idx]
        
        # Determine if we are ahead or behind the beat
        # normalized phase in [0, 1)
        phase = ((t - nearest_beat) / beat_period) % 1.0
        
        # check zones [0.15, 0.35] and [0.65, 0.85]
        # (0.25 +/- 0.1 and 0.75 +/- 0.1)
        if (0.15 <= phase <= 0.35) or (0.65 <= phase <= 0.85):
            hits += 1

    syncopation_score = hits / total if total > 0 else 0.0
    return round(float(syncopation_score), 4)


def compute_pulse_clarity(onset_envelope, sr: int, hop_length: int, bpm: float) -> float:
    """
    Pulse Clarity — Autocorrelation of onset strength at the beat lag.
    """
    import numpy as np
    onset_envelope = np.asarray(onset_envelope, dtype=float)
    if len(onset_envelope) < 10 or bpm <= 0:
        return 0.0

    # Normalised autocorrelation
    acf = np.correlate(onset_envelope, onset_envelope, mode="full")
    acf = acf[len(acf)//2:]
    acf /= (acf[0] + 1e-8)

    # Convert BPM to lag in frames
    beat_lag = int(round((sr / hop_length) * (60.0 / bpm)))
    
    if beat_lag >= len(acf):
        return 0.0
    
    # Check a small window around the lag for the peak
    window = acf[max(0, beat_lag-2) : min(len(acf), beat_lag+3)]
    clarity = np.max(window) if len(window) > 0 else 0.0
    
    return round(float(np.clip(clarity, 0.0, 1.0)), 4)


def compute_log_drum_score(sub_bass_ratio: float, avg_centroid: float) -> float:
    """
    Combines sub-bass dominance and spectral centroid into a single log drum score.
    Higher ratio + Lower centroid = Stronger log drum presence.
    """
    # Normalize inputs (based on observed Amapiano vs Pop distributions)
    # Ratio expected range: 0.1 (low) to 0.4 (high Amapiano)
    # Centroid expected range: 1000 (deep) to 5000 (bright)
    
    import numpy as np
    norm_ratio = np.clip((sub_bass_ratio - 0.1) / 0.3, 0.0, 1.0)
    norm_centroid = 1.0 - np.clip((avg_centroid - 800) / 3000, 0.0, 1.0)
    
    score = (0.7 * norm_ratio) + (0.3 * norm_centroid)
    return round(float(score), 4)


def compute_custom_danceability(complexity, syncopation, clarity, log_drum=0.0):
    """
    Revised for Amapiano/Afrobeats v1.3.0
    
    High pulse clarity = strong beat (0.50 weight)
    High syncopation = groove/swing (0.30 weight)
    Log Drum Presence = Cultural signifier (0.20 weight)
    
    Polyrhythms ARE the groove, not a penalty.
    """
    if any(x is None for x in [complexity, syncopation, clarity]):
        return None
    
    score = (0.50 * clarity) + (0.30 * syncopation) + (0.20 * log_drum)
    
    return round(float(max(0.0, min(1.0, score))), 4)


# ── Extraction Logic ─────────────────────────────────────────────────────────

def _get_onset_envelope(audio, sr, hop_length):
    import librosa
    return librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop_length)


def extract_with_essentia(file_path: Path) -> dict:
    import essentia.standard as es
    import numpy as np

    loader = es.MonoLoader(filename=str(file_path), sampleRate=44100)
    # Only load first 120 seconds for analysis (BPM/Spectral)
    # 44100 * 120 = 5,292,000
    audio = loader()
    if len(audio) > 5292000:
        audio = audio[:5292000]
    SR = 44100
    HOP = 512

    # BPM & Beats
    rhythm = es.RhythmExtractor2013(method="multifeature")
    bpm, beats, confidence, _, _ = rhythm(audio)

    # RMS Energy
    rms_algo = es.RMS()
    rms_vals = [float(rms_algo(f)) for f in es.FrameGenerator(audio, frameSize=2048, hopSize=HOP)]
    energy_rms = float(np.mean(rms_vals))

    # Onsets
    onset_det = es.OnsetRate()
    onset_times, onset_rate = onset_det(audio)

    # ── Spectral Analysis (Phase 5) ──────────────
    spectrum = es.Spectrum()
    window = es.Windowing(type="hann")
    centroid_algo = es.Centroid()
    energy_band_low = es.EnergyBand(startCutoffFrequency=30, stopCutoffFrequency=120)
    energy_band_full = es.EnergyBand(startCutoffFrequency=30, stopCutoffFrequency=20000)
    
    centroids = []
    low_energies = []
    full_energies = []

    # Process frames for spectral info (Limited to 60s window to speed up processing)
    # Target middle of the track (30s to 90s), or start if too short
    duration = len(audio) / SR
    start_sec = 30 if duration > 40 else 0
    end_sec = start_sec + 60
    
    start_frame = int(start_sec * SR / HOP)
    end_frame = int(end_sec * SR / HOP)
    
    frame_gen = es.FrameGenerator(audio, frameSize=2048, hopSize=HOP)
    for i, frame in enumerate(frame_gen):
        if i < start_frame: continue
        if i > end_frame: break
        
        spec = spectrum(window(frame))
        centroids.append(centroid_algo(spec))
        low_energies.append(energy_band_low(spec))
        full_energies.append(energy_band_full(spec))

    sub_bass_ratio = np.mean(low_energies) / (np.mean(full_energies) + 1e-8)
    
    # Calculate centroid ONLY at onset times (approximate frames)
    onset_frames = [int(round(t * SR / HOP)) for t in onset_times]
    onset_centroids = [centroids[min(f, len(centroids)-1)] for f in onset_frames]
    avg_onset_centroid = np.mean(onset_centroids) if onset_centroids else np.mean(centroids)

    log_drum_presence = compute_log_drum_score(sub_bass_ratio, avg_onset_centroid)

    # Groove Features
    envelope = _get_onset_envelope(np.array(audio), SR, HOP)
    complexity = compute_rhythmic_complexity(onset_times)
    syncopation = compute_syncopation(onset_times, beats)
    clarity = compute_pulse_clarity(envelope, SR, HOP, bpm)
    danceability = compute_custom_danceability(complexity, syncopation, clarity, log_drum_presence)

    return {
        "bpm": bpm, "confidence": confidence, "energy": energy_rms,
        "onsets": onset_rate, "duration": len(audio)/SR, "backend": "essentia",
        "groove": {
            "rhythmic_complexity": complexity,
            "syncopation": syncopation,
            "pulse_clarity": clarity,
            "log_drum_presence": log_drum_presence,
            "danceability_custom": danceability
        }
    }


def extract_with_librosa(file_path: Path) -> dict:
    import librosa
    import numpy as np
    
    audio, sr = librosa.load(str(file_path), sr=None, mono=True)
    HOP = 512
    
    tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr, hop_length=HOP)
    bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
    beats = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP)
    
    rms = librosa.feature.rms(y=audio, hop_length=HOP)
    energy_rms = float(np.mean(rms))
    
    onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, hop_length=HOP)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP)
    onset_rate = len(onset_times) / (len(audio)/sr)

    envelope = _get_onset_envelope(audio, sr, HOP)
    complexity = compute_rhythmic_complexity(onset_times)
    syncopation = compute_syncopation(onset_times, beats)
    clarity = compute_pulse_clarity(envelope, sr, HOP, bpm)
    # Librosa fallback doesn't do spectral analysis yet, so log_drum=0
    danceability = compute_custom_danceability(complexity, syncopation, clarity, 0.0)

    return {
        "bpm": bpm, "confidence": None, "energy": energy_rms,
        "onsets": onset_rate, "duration": len(audio)/sr, "backend": "librosa",
        "groove": {
            "rhythmic_complexity": complexity,
            "syncopation": syncopation,
            "pulse_clarity": clarity,
            "log_drum_presence": 0.0,
            "danceability_custom": danceability
        }
    }


# ── Main extraction orchestrator ───────────────────────────────────────────────

def extract_features(file_path: Path) -> dict:
    """Try Essentia first; fall back to librosa on any failure."""
    try:
        return extract_with_essentia(file_path)
    except Exception:
        return extract_with_librosa(file_path)


def build_result(file_path: Path, res: dict) -> dict:
    """Wrap raw features in a structured result envelope."""
    return {
        "file": str(file_path.resolve()),
        "file_name": file_path.name,
        "format": file_path.suffix.lower().lstrip("."),
        "features": {
            "tempo_bpm": round(res["bpm"], 2),
            "beats_confidence": round(res["confidence"], 4) if res["confidence"] else None,
            "energy_rms": round(res["energy"], 6),
            "onset_rate_per_second": round(res["onsets"], 4),
            "duration_seconds": round(res["duration"], 3),
            "groove": res["groove"]
        },
        "metadata": {
            "backend": res["backend"],
            "version": "1.3.0",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_file")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    try:
        path = validate_file(args.audio_file)
        try:
            res = extract_with_essentia(path)
        except Exception as e:
            log.warning(f"Essentia failed, trying librosa: {e}")
            res = extract_with_librosa(path)

        output = {
            "file": str(path.name),
            "features": {
                "tempo_bpm": round(res["bpm"], 2),
                "energy_rms": round(res["energy"], 6),
                "onset_rate": round(res["onsets"], 4),
                "groove": res["groove"]
            },
            "metadata": {"backend": res["backend"], "version": "1.3.0"}
        }

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2)
        else:
            print(json.dumps(output, indent=2))

    except Exception as e:
        log.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
