"""
Music Analysis Module for Auto-Cue System

Analyzes audio in real-time to detect:
1. Musical sections (STROPHE, REFRAIN, BREAK)
2. Song changes (spectral profile shifts)

Used by auto_cue_engine.py to determine WHEN cue transitions are allowed.
"""

from __future__ import annotations
from typing import Dict, Optional, List
import time
import math

_LOG_PREFIX = "[music_analyzer]"
print(f"{_LOG_PREFIX} module loaded")

# Thresholds for section classification
REFRAIN_THRESH = 0.6  # Refrain needs high energy
BREAK_THRESH = 0.3    # Break needs low rhythm activity

# Song detection parameters
PROFILE_WINDOW_SEC = 5.0  # Average spectral features over 5 seconds
PROFILE_DIST_THRESH = 0.4  # Distance threshold for "new song"

# Internal state
_section_history: List[Dict] = []  # Recent section detections
_current_section: str = "STROPHE"
_section_start_time: float = 0.0
_last_section_change: float = 0.0

_active_profile: Optional[List[float]] = None  # Current song profile
_profile_buffer: List[Dict] = []  # Buffer for profile averaging
_last_song_change: float = 0.0


def _calculate_section_scores(audio_values: Dict[str, float]) -> Dict[str, float]:
    """Calculate scores for each section type based on audio features.

    Args:
        audio_values: Dict with keys: low, mid, high, kick, snare, rhythm

    Returns:
        Dict with keys: refrain_score, strophe_score, break_score
    """
    # Extract audio features
    low = audio_values.get('low', 0.0)
    mid = audio_values.get('mid', 0.0)
    high = audio_values.get('high', 0.0)
    kick = audio_values.get('kick', 0.0)
    snare = audio_values.get('snare', 0.0)
    rhythm = audio_values.get('rhythm', 0.0)

    # Calculate rhythm activity
    rhythm_activity = kick + snare + rhythm

    # Section scores
    # Refrain: Full spectrum (bass + treble) + high energy
    refrain_score = (low * high * 2.0) + rhythm_activity

    # Strophe: Mid-focused with moderate groove
    strophe_score = mid + (rhythm_activity * 0.5)

    # Break: Low energy, minimal rhythm
    break_score = (low + mid) * (1.0 - rhythm_activity)

    return {
        'refrain_score': refrain_score,
        'strophe_score': strophe_score,
        'break_score': break_score,
    }


def _classify_section(scores: Dict[str, float]) -> str:
    """Classify section based on scores with priority: REFRAIN > BREAK > STROPHE.

    Args:
        scores: Dict with refrain_score, strophe_score, break_score

    Returns:
        Section name: "REFRAIN", "BREAK", or "STROPHE"
    """
    refrain = scores['refrain_score']
    strophe = scores['strophe_score']
    break_s = scores['break_score']

    # Priority: REFRAIN > BREAK > STROPHE
    if refrain > REFRAIN_THRESH and refrain >= break_s and refrain >= strophe:
        return "REFRAIN"
    elif break_s > BREAK_THRESH and break_s >= strophe:
        return "BREAK"
    else:
        return "STROPHE"


def _check_section_confidence(candidate: str, confidence_ms: float) -> bool:
    """Check if section candidate has been stable for required time.

    Args:
        candidate: Candidate section name
        confidence_ms: Required stability time in milliseconds

    Returns:
        True if candidate has been stable for confidence_ms
    """
    global _section_history

    current_time = time.time()
    confidence_sec = confidence_ms / 1000.0

    # Check if all recent history entries match candidate
    stable_since = current_time
    for entry in reversed(_section_history):
        if entry['section'] != candidate:
            break
        stable_since = entry['timestamp']

    stable_duration = current_time - stable_since
    return stable_duration >= confidence_sec


def _update_song_profile(audio_values: Dict[str, float], current_time: float) -> Optional[bool]:
    """Update spectral profile buffer and check for song changes.

    Args:
        audio_values: Dict with spectral features
        current_time: Current timestamp

    Returns:
        True if new song detected, False if same song, None if not enough data yet
    """
    global _active_profile, _profile_buffer, _last_song_change

    # Extract spectral features
    spectral_centroid = audio_values.get('spectralCentroid', 0.0)
    fmsd = audio_values.get('fmsd', 0.0)
    smsd = audio_values.get('smsd', 0.0)

    # Add to buffer
    _profile_buffer.append({
        'timestamp': current_time,
        'centroid': spectral_centroid,
        'fmsd': fmsd,
        'smsd': smsd,
    })

    # Remove old entries (older than PROFILE_WINDOW_SEC)
    cutoff = current_time - PROFILE_WINDOW_SEC
    _profile_buffer = [e for e in _profile_buffer if e['timestamp'] > cutoff]

    # Need at least 2 seconds of data
    if len(_profile_buffer) < 60:  # ~60 frames at 30fps = 2 seconds
        return None

    # Calculate current profile (average over window)
    current_profile = [
        sum(e['centroid'] for e in _profile_buffer) / len(_profile_buffer),
        sum(e['fmsd'] for e in _profile_buffer) / len(_profile_buffer),
        sum(e['smsd'] for e in _profile_buffer) / len(_profile_buffer),
    ]

    # First profile? Just store it
    if _active_profile is None:
        _active_profile = current_profile
        _last_song_change = current_time
        return False

    # Calculate euclidean distance
    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(current_profile, _active_profile)))

    # New song detected?
    if distance > PROFILE_DIST_THRESH:
        print(f"{_LOG_PREFIX} 🎵 NEW SONG DETECTED (spectral distance={distance:.3f})")
        _active_profile = current_profile
        _last_song_change = current_time
        return True

    return False


def analyze(
    audio_chop,
    confidence_ms: float,
    min_section_time_sec: float,
    cooldown_sec: float,
    song_cooldown_sec: float,
) -> Dict:
    """Main analysis function - called every frame.

    Args:
        audio_chop: Audio analysis CHOP with channels
        confidence_ms: Required stability time for section changes (CH18)
        min_section_time_sec: Minimum time before allowing section change (CH16 in AutoCue)
        cooldown_sec: Cooldown after last transition (CH17)
        song_cooldown_sec: Minimum time between song change detections (CH19)

    Returns:
        Dict with analysis results:
        {
            'current_section': str,           # Current section name
            'section_stable_ms': float,       # How long section has been stable
            'new_song_detected': bool,        # True if new song just detected
            'allow_transition': bool,         # True if transition is allowed now
            'scores': Dict[str, float],       # Raw scores for debugging
        }
    """
    global _section_history, _current_section, _section_start_time, _last_section_change

    current_time = time.time()

    # Extract audio values from CHOP
    audio_values = {}
    if audio_chop and audio_chop.numSamples > 0:
        for ch in audio_chop.chans():
            audio_values[ch.name] = ch[0]

    # Calculate section scores
    scores = _calculate_section_scores(audio_values)

    # Classify section
    candidate = _classify_section(scores)

    # Add to history
    _section_history.append({
        'timestamp': current_time,
        'section': candidate,
    })

    # Keep only last 5 seconds of history
    cutoff = current_time - 5.0
    _section_history = [e for e in _section_history if e['timestamp'] > cutoff]

    # Check if candidate is stable enough
    is_confident = _check_section_confidence(candidate, confidence_ms)

    # Check if section actually changed
    section_changed = False
    if is_confident and candidate != _current_section:
        # Section wants to change - check timing constraints
        time_since_section_start = current_time - _section_start_time
        time_since_last_change = current_time - _last_section_change

        if time_since_section_start >= min_section_time_sec and time_since_last_change >= cooldown_sec:
            # All conditions met - accept section change
            print(f"{_LOG_PREFIX} Section change: {_current_section} -> {candidate}")
            _current_section = candidate
            _section_start_time = current_time
            _last_section_change = current_time
            section_changed = True

    # Calculate how long current section has been stable
    section_stable_ms = (current_time - _section_start_time) * 1000.0

    # Check for song changes
    new_song_raw = _update_song_profile(audio_values, current_time)
    new_song_allowed = False

    # Respect song cooldown for actual song change events
    if new_song_raw:
        time_since_last_song = current_time - _last_song_change
        if time_since_last_song < song_cooldown_sec:
            print(f"{_LOG_PREFIX} Song change detected but suppressed by cooldown ({time_since_last_song:.1f}s < {song_cooldown_sec:.1f}s)")
            # Still allow mapping reset even if cooldown prevents full song change
            new_song_allowed = False
        else:
            new_song_allowed = True

    # Determine if transition is allowed
    # In AutoCue mode, allow transition on section change OR after long stability
    allow_transition = section_changed

    return {
        'current_section': _current_section,
        'section_stable_ms': section_stable_ms,
        'new_song_detected': new_song_allowed,
        'new_song_detected_raw': new_song_raw if new_song_raw is not None else False,  # Raw detection, ignoring cooldown
        'allow_transition': allow_transition,
        'scores': scores,
    }


def reset():
    """Reset all analyzer state (useful for testing or manual restart)."""
    global _section_history, _current_section, _section_start_time, _last_section_change
    global _active_profile, _profile_buffer, _last_song_change

    _section_history.clear()
    _current_section = "STROPHE"
    _section_start_time = time.time()
    _last_section_change = time.time()

    _active_profile = None
    _profile_buffer.clear()
    _last_song_change = time.time()

    print(f"{_LOG_PREFIX} State reset")


def get_state() -> Dict:
    """Get current analyzer state for debugging."""
    return {
        'current_section': _current_section,
        'section_start_time': _section_start_time,
        'last_section_change': _last_section_change,
        'active_profile': _active_profile,
        'profile_buffer_size': len(_profile_buffer),
        'last_song_change': _last_song_change,
    }
