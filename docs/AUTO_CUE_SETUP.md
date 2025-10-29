# Auto-Cue System Setup Guide

## Overview

The Auto-Cue system enables automatic, music-driven cue playback in EOS based on real-time audio analysis from TouchDesigner.

**Key Features:**
- **Timer Mode**: Regular interval-based cue switching (simple)
- **AutoCue Mode**: Music-driven cue switching (intelligent)
- **Song Recognition**: Automatic history reset on song changes
- **Cue History**: Smart repetition (no direct repeats, sane repetition over time)
- **Pool Control**: EOS defines which cues are available (via DMX CH3-8)

---

## Architecture

```
┌─────────────┐
│    EOS      │  Defines: Cuelist, StartCue, EndCue (CH3-8)
└──────┬──────┘           Pool of available cues
       │ DMX
       ▼
┌─────────────────────┐
│  TouchDesigner      │
│  ┌───────────────┐  │
│  │ music_analyzer│  │  Analyzes: Sections, Song changes
│  └───────┬───────┘  │
│          ▼          │
│  ┌───────────────┐  │
│  │auto_cue_engine│  │  Selects: Random cue from pool
│  └───────┬───────┘  │           Maintains history
│          │          │
│          ▼  OSC     │
└──────────┼──────────┘
           │
           ▼
      ┌─────────┐
      │   EOS   │  Fires: /eos/cue/{list}/{cue}/fire
      └─────────┘
```

---

## DMX Parameter Reference

### Pool Definition (Set by EOS/Operator)

| Channel | Parameter | Range | Description |
|---------|-----------|-------|-------------|
| CH3-4 | Cuelist | 0-999 | Which cuelist to use (16-bit) |
| CH5-6 | StartCue | 0-999 | First cue in allowed range (16-bit) |
| CH7-8 | EndCue | 0-999 | Last cue in allowed range (16-bit) |

**Example:** Cuelist=5, StartCue=20, EndCue=35
- TouchDesigner will only fire cues 20-35 from cuelist 5
- EOS defines this pool, TouchDesigner respects it

### Behavior Control (Set by TouchDesigner or Operator)

| Channel | Parameter | DMX Range | Real Value | Description |
|---------|-----------|-----------|------------|-------------|
| **CH15** | **AdvanceMode** | 0-84 | OFF | No auto-cue (submaster control only) |
| | | 85-169 | TIMER | Time-based random cues |
| | | 170-255 | AUTOCUE | Music-driven cues |
| **CH16** | **MinSectionTime** | 0-255 | 1-100s | Timer: Interval<br>AutoCue: Min cue hold time |
| **CH17** | **CooldownAfterSwitch** | 0-255 | 1-100s | Cooldown after cue switch |
| **CH18** | **RequireConfidenceFrames** | 0-255 | 0-2550ms | Signal stability before switch |
| **CH19** | **SongCooldownTime** | 0-255 | 1-990s | Min time between song resets |

---

## Setup Instructions

### Step 1: Verify DMX Patch (19 Channels)

Check that your S2L_UNIT instances use the 19-channel patch:

```python
# In TouchDesigner textport:
import sys
sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src')
from s2l_unit import dmx_map as s2l
print(f"DMX slots per instance: {s2l.DMX_SLOTS_PER_INSTANCE}")
# Should print: 19
```

### Step 2: Verify Instance Configuration

Check `config/s2l_unit/instances.csv`:

```csv
instance,enabled,universe,start_address
S2L_UNIT_1,true,16,1
S2L_UNIT_2,true,16,20
S2L_UNIT_3,true,16,39
...
```

**Spacing:** 19 channels per unit (1, 20, 39, 58, 77, ...)

### Step 3: Create Auto-Cue Execute DAT

1. In TouchDesigner, navigate to `/project1/src/s2l_manager/`
2. Create new **DAT > Execute DAT**
3. Name it: `auto_cue_exec`
4. In the Execute DAT parameters:
   - **DATs** tab: (leave empty)
   - **CHOPs** tab: (leave empty)
   - **Execute** tab:
     - Enable: `Frame Start`
     - Set: `onFrameStart`

5. Click the **Edit** button (or press F1 with DAT selected)
6. Delete default content
7. Copy entire contents of `src/s2l_manager/auto_cue_exec.py`
8. Paste into the Execute DAT editor
9. Save (Ctrl+S)

### Step 4: Verify Operator Paths

Check that these operators exist:

```python
# In textport:
print(op('/project1/src/s2l_manager/values'))
print(op('/project1/s2l_audio/fixutres/audio_analysis'))
print(op('/project1/io/oscout1'))
```

If any are `None`, update the paths in `auto_cue_exec.py`:
- `VALUES_TABLE_PATH`
- `AUDIO_CHOP_PATH`

### Step 5: Configure EOS for OSC

In EOS:
1. Go to **Setup > System Settings > Show Control > OSC**
2. Enable **OSC RX** (receive)
3. Note the **RX Port** (usually 3032)
4. Add TouchDesigner IP to **Allowed IPs**

In TouchDesigner:
1. Find `/project1/io/oscout1` (OSC Out CHOP or DAT)
2. Set **Network Address** to EOS IP
3. Set **Network Port** to 3032 (or your RX port)

### Step 6: Set Initial Parameters

For testing, set these values in EOS via DMX (or manually in values table):

**For S2L_UNIT_1:**
- `Cuelist` (CH3-4): 5 (or your test cuelist)
- `StartCue` (CH5-6): 1
- `EndCue` (CH7-8): 10
- `AutoCueMode` (CH15): 100 (TIMER mode)
- `MinSectionTime` (CH16): 128 (≈50s interval)
- `CooldownAfterSwitch` (CH17): 64 (≈25s)
- `RequireConfidenceFrames` (CH18): 100 (≈1000ms)
- `SongCooldownTime` (CH19): 128 (≈500s)

---

## Testing

### Test 1: Verify Configuration

```python
# In textport:
exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
exec_dat.module.show_config()
```

**Expected output:**
```
================================================================================
AUTO-CUE EXEC CONFIGURATION
================================================================================
Enabled: True
Values table: /project1/src/s2l_manager/values
Audio CHOP: /project1/s2l_audio/fixutres/audio_analysis
...
Operator Status:
  Values table: ✅ Found
  Audio CHOP: ✅ Found
  OSC output: ✅ Found
```

### Test 2: Test Music Analyzer

```python
exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
exec_dat.module.test_analyzer()
```

**Expected output:**
```
================================================================================
MUSIC ANALYZER TEST
================================================================================
Current section: STROPHE
Section stable: 2450ms
New song detected: False
Allow transition: False

Scores:
  refrain_score: 0.423
  strophe_score: 0.651
  break_score: 0.234
```

### Test 3: Test Auto-Cue for Unit

```python
exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
exec_dat.module.test_unit("S2L_UNIT_1")
```

**Expected output:**
```
================================================================================
AUTO-CUE ENGINE TEST: S2L_UNIT_1
================================================================================
Parameters from values table:
  AutoCueMode               = 100 (TIMER)
  MinSectionTime            = 128 (50.5s)
  Cuelist                   = 5
  StartCue                  = 1
  EndCue                    = 10
  ...

Current state:
  mode                 = TIMER
  current_cue          = 7
  cue_history          = [3, 7]
  last_fire_time       = 15.3s ago
  cuelist              = 5
  ...
```

### Test 4: Timer Mode (Live Test)

1. Set CH15 = 100 (TIMER)
2. Set CH16 = 50 (≈20s interval)
3. Set CH3-4 = 5 (Cuelist 5)
4. Set CH5-6 = 1, CH7-8 = 5 (Cues 1-5)
5. Watch textport for:
   ```
   [auto_cue_engine] Fired cue 3 in cuelist 5
   [auto_cue_engine] Fired cue 1 in cuelist 5
   [auto_cue_engine] Fired cue 5 in cuelist 5
   ```
6. Verify in EOS that cues are firing
7. Note: No direct repeats (no "cue 3" twice in a row)

### Test 5: AutoCue Mode (Live Test)

1. Set CH15 = 200 (AUTOCUE)
2. Set CH16 = 128 (≈50s min hold time)
3. Set CH17 = 64 (≈25s cooldown)
4. Set CH18 = 100 (≈1000ms confidence)
5. Play music with clear sections (Verse/Chorus/Drop)
6. Watch textport for:
   ```
   [music_analyzer] Section change: STROPHE -> REFRAIN
   [auto_cue_engine] Fired cue 7 in cuelist 5
   ```
7. Cues should fire on musical transitions, not randomly

---

## Troubleshooting

### No Cues Firing

**Check:**
1. Is `ENABLE_PROCESSING = True` in `auto_cue_exec.py`?
2. Are CH3-8 set correctly (Cuelist, StartCue, EndCue)?
3. Is CH15 > 84 (Timer or AutoCue mode)?
4. Is OSC output working? (Test with manual OSC send)
5. Check textport for errors

**Debug command:**
```python
exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
exec_dat.module.test_unit("S2L_UNIT_1")
```

### Cues Fire Too Fast

**Solution:**
- Increase CH16 (MinSectionTime) - makes cues hold longer
- Increase CH17 (CooldownAfterSwitch) - adds delay after switch
- In AutoCue: Increase CH18 (Confidence) - requires more stable signal

### Cues Fire Too Slow

**Solution:**
- Decrease CH16 (MinSectionTime)
- Decrease CH17 (CooldownAfterSwitch)
- In AutoCue: Lower `REFRAIN_THRESH` / `BREAK_THRESH` in `music_analyzer.py`

### Same Cue Repeats Immediately

**Check:**
- Is pool size > 1? (EndCue must be > StartCue)
- Check `cue_history` in test output
- If history is empty, engine isn't tracking properly

**Debug:**
```python
import auto_cue_engine
state = auto_cue_engine.get_unit_state("S2L_UNIT_1")
print(state['cue_history'])
```

### Song Detection Too Sensitive

**Solution:**
- Increase `PROFILE_DIST_THRESH` in `music_analyzer.py` (default 0.4 → try 0.6)
- Increase CH19 (SongCooldownTime)

### Song Detection Not Working

**Solution:**
- Decrease `PROFILE_DIST_THRESH` (0.4 → 0.3)
- Check audio analysis has spectral features:
  ```python
  audio = op('/project1/s2l_audio/fixutres/audio_analysis')
  print([ch.name for ch in audio.chans()])
  # Should include: spectralCentroid, fmsd, smsd
  ```

---

## Advanced Configuration

### Tuning Section Detection

Edit `music_analyzer.py`:

```python
# More sensitive refrain detection
REFRAIN_THRESH = 0.5  # Lower = easier to trigger (default 0.6)

# More sensitive break detection
BREAK_THRESH = 0.35  # Higher = easier to trigger (default 0.3)
```

### Adjusting History Length

Edit `auto_cue_engine.py`:

```python
# Remember more cues (less repetition)
HISTORY_LENGTH = 6  # Default: 4

# In _select_next_cue(), adjust recent history window:
recent_history = state.get('cue_history', [])[-3:]  # Last 3 cues (default: 2)
```

### Custom Parameter Scaling

Edit scaling functions in `auto_cue_engine.py`:

```python
def _scale_ch16(dmx_value: int) -> float:
    """Scale CH16 to 1-120s instead of 1-100s."""
    return 1.0 + (dmx_value / 255.0) * 119.0
```

---

## API Reference

### music_analyzer Module

```python
import music_analyzer

# Analyze current frame
result = music_analyzer.analyze(
    audio_chop=audio_chop,
    confidence_ms=1000.0,
    min_section_time_sec=8.0,
    cooldown_sec=3.0,
    song_cooldown_sec=30.0,
)

# Returns:
# {
#     'current_section': 'REFRAIN',
#     'section_stable_ms': 2400.0,
#     'new_song_detected': False,
#     'allow_transition': True,
#     'scores': {...}
# }

# Reset state
music_analyzer.reset()

# Get current state
state = music_analyzer.get_state()
```

### auto_cue_engine Module

```python
import auto_cue_engine

# Process single unit
fired = auto_cue_engine.process_unit(
    unit_name="S2L_UNIT_1",
    values_table=values_table,
    analyzer_output=analyzer_output,
    current_time=time.time(),
)

# Process all units
count = auto_cue_engine.process_all_units(
    values_table=values_table,
    analyzer_output=analyzer_output,
)

# Get unit state
state = auto_cue_engine.get_unit_state("S2L_UNIT_1")

# Clear history
auto_cue_engine.clear_all_history()

# Reset engine
auto_cue_engine.reset()
```

---

## Workflow Examples

### Example 1: Simple Timer Show

**Goal:** Random cues every 30 seconds from cuelist 5, cues 1-20

**Setup:**
- CH3-4 (Cuelist): 5
- CH5-6 (StartCue): 1
- CH7-8 (EndCue): 20
- CH15 (Mode): 100 (TIMER)
- CH16 (Interval): 77 (≈30s)

**Result:** Cues fire every 30s, random from 1-20, no direct repeats

---

### Example 2: Music-Reactive Show

**Goal:** Cues change on drops/transitions, hold at least 10s

**Setup:**
- CH3-4 (Cuelist): 7
- CH5-6 (StartCue): 10
- CH7-8 (EndCue): 25
- CH15 (Mode): 200 (AUTOCUE)
- CH16 (MinHold): 26 (≈10s)
- CH17 (Cooldown): 20 (≈8s)
- CH18 (Confidence): 80 (≈800ms)

**Result:** Cues fire on STROPHE→REFRAIN, REFRAIN→BREAK transitions, respecting timing constraints

---

### Example 3: Song-Aware DJ Set

**Goal:** Each track gets "fresh" cue selection

**Setup:**
- Same as Example 2, but also:
- CH19 (SongCooldown): 64 (≈250s)

**Result:**
- When new track is detected (spectral profile changes), cue history clears
- Each song gets its own "mix" of cues from the same pool
- But not every transition is treated as new song (250s cooldown)

---

## Performance Notes

- **Frame Rate**: System runs every frame (30-60fps typical)
- **CPU Usage**: Light (music analysis is optimized)
- **OSC Rate**: Cues fire only when conditions met (not every frame)
- **Memory**: Minimal (history ~4-6 cues per unit)

---

## Changelog

### Version 1.0 (2025-01-XX)
- Initial implementation
- Timer and AutoCue modes
- Music analysis (section detection, song recognition)
- Cue history management
- 19-channel DMX patch support
