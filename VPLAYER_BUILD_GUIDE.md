# Video Player Build Guide - TouchDesigner Implementation

Complete step-by-step guide for building the `/vplayer` component in TouchDesigner.

## Overview

This guide builds a professional video player that:
- Follows Eos lighting console passively (no OSC output from TD)
- Uses marker-based cue synchronization
- Has two modes: FOLLOW (default) and RECORD (marker editing)
- Integrates with existing MIDICRAFT ENC hardware
- Operates entirely with CHOPs/DATs (minimal Python)

**Time Estimate:** 2.5-3 hours

---

## Prerequisites

✅ **Already Completed:**
- [menus/menu_5/map_osc.tsv](menus/menu_5/map_osc.tsv) updated with fader mappings
- [menus/menu_engine.py](menus/menu_engine.py) event handler added
- Python scripts created in `vplayer_scripts/`

**Required:**
- TouchDesigner 2023.11760 or later
- Existing MIDICRAFT ENC setup working
- Eos OSC feedback configured (see OSC_IN_GUIDE.md)

---

## Part 1: Base Component Structure

### 1.1 Create Base COMP

1. Navigate to `/project1/media/`
2. Create new **Base COMP**:
   - Right-click → `Operators` → `COMP` → `Base COMP`
   - Name: `vplayer`
3. Enter the `vplayer` component (double-click)

### 1.2 Create State CHOPs

Inside `/project1/media/vplayer`:

**State CHOP** (player state):
1. Create **Constant CHOP**
2. Name: `state`
3. Parameters:
   - Channels: `5`
   - Channel Names: `mode speed volume loop scrub_value`
   - Channel Values:
     - `mode`: `0` (0=FOLLOW, 1=RECORD)
     - `speed`: `1.0`
     - `volume`: `0.8`
     - `loop`: `0`
     - `scrub_value`: `0`

**Eos State CHOP** (Eos feedback):
1. Create **Constant CHOP**
2. Name: `eos_state`
3. Parameters:
   - Channels: `5`
   - Channel Names: `active_list active_cue pending_list pending_cue progress`
   - All values: `0`

### 1.3 Create Markers Table

1. Create **Table DAT**
2. Name: `markers`
3. Parameters:
   - Rows: `1`
   - Cols: `3`
   - Row 0 Pre-fill: `key	pos_s	label`
   - Enable "First Row is Header": ✅

This table will store: `key` (cue), `pos_s` (seconds), `label` (display name)

---

## Part 2: Video and Audio Chain

### 2.1 Movie File In TOP

1. Create **Movie File In TOP**
2. Name: `moviefilein1`
3. Parameters:
   - **File Tab:**
     - File: (leave empty for now, will be set per show)
     - Index Mode: `Cue Point Seconds`
     - Cue Point Seconds: (leave default, will be controlled)
   - **Play Tab:**
     - Play: `On` (always playing)
     - Speed: Expression → `op('state')['speed']`
     - Loop: Expression → `op('state')['loop']`
     - Cue: (pulse parameter, controlled by scripts)
4. Create **Null TOP**
   - Name: `null_vid1`
   - Input: Connect from `moviefilein1`
5. Create **Out TOP**
   - Name: `out1`
   - Input: Connect from `null_vid1`

### 2.2 Audio Chain

1. Create **Audio Movie CHOP**
   - Name: `audiomovie1`
   - Parameters:
     - Movie File TOP: `moviefilein1`
2. Create **Audio Device Out CHOP**
   - Name: `audiodeviceout1`
   - Input: Connect from `audiomovie1`
   - Parameters:
     - Driver: `Direct Sound` (Windows) or appropriate for your OS
     - Volume: Expression → `op('state')['volume']`

### 2.3 Info CHOP

1. Create **Info CHOP**
   - Name: `info_video`
   - Parameters:
     - Operator: `moviefilein1`
2. This provides: `position_seconds`, `length_seconds`, etc.

---

## Part 3: Fader Integration (Scrub/Speed/Volume)

### 3.1 Scrub Input (Fader 1)

Create CHOP network for scrubbing:

1. **Constant CHOP**:
   - Name: `scrub_input`
   - Channels: `1`
   - Value: `0`
   - *Note: This is written to by menu_engine.py*

2. **Math CHOP** (convert 0-1 to seconds):
   - Name: `scrub_to_seconds`
   - Input: `scrub_input`
   - Combine Channels: `Multiply`
   - Mult: Expression → `op('info_video')['length_seconds']`

3. **CHOP Execute DAT**:
   - Name: `scrub_execute`
   - CHOP: `scrub_to_seconds`
   - Code:
```python
def onValueChange(channel, sampleIndex, val, prev):
    # On scrub fader change, jump video
    moviefile = op('../moviefilein1')
    if moviefile and abs(val - prev) > 0.01:  # Debounce small changes
        moviefile.par.cuepointseconds = val
        moviefile.par.cue.pulse()
```

### 3.2 Speed Input (Fader 2)

1. **Constant CHOP**:
   - Name: `speed_input`
   - Value: `1.0`
   - *Note: Written to by menu_engine.py, already bound to moviefilein1.speed*

### 3.3 Volume Input (Fader 3)

1. **Constant CHOP**:
   - Name: `volume_input`
   - Value: `0.8`
   - *Note: Written to by menu_engine.py, already bound to audiodeviceout1.volume*

---

## Part 4: OSC Event Handlers

### 4.1 OSC Event Handler Script DAT

1. Create **Text DAT**
   - Name: `osc_event_handler`
2. Open external editor and copy content from:
   - `vplayer_scripts/osc_event_handler.py`
3. Paste into DAT

### 4.2 OSC In Integration

*Detailed in OSC_IN_GUIDE.md, but quick setup:*

1. Navigate to your OSC In setup (likely `/project1/io/` or similar)
2. Find **OSC In DAT** or **OSC In MAP CHOP**
3. Add callback to DAT's `onReceiveOSC`:

```python
def onReceiveOSC(dat, rowIndex, message, bytes):
    address = message[0]
    args = message[1:]

    # Route to vplayer handler
    handler = op('/project1/media/vplayer/osc_event_handler')
    if handler and handler.module:
        handler.module.on_osc_message(address, *args)
```

**Or** if using OSC In MAP CHOP, create channel-specific callbacks for:
- `/eos/out/active/cue/*/*` → calls `osc_event_handler.on_active_cue_change(list, cue)`
- `/eos/out/pending/cue/*/*` → calls `osc_event_handler.on_pending_cue_change(list, cue)`
- `/eos/out/active/cue` (float) → calls `osc_event_handler.on_progress_update(val)`

---

## Part 5: RECORD Mode Scripts

### 5.1 Marker Write Script

1. Create **Text DAT**
   - Name: `marker_write`
2. Copy content from: `vplayer_scripts/marker_write.py`

### 5.2 Marker Delete Script

1. Create **Text DAT**
   - Name: `marker_delete`
2. Copy content from: `vplayer_scripts/marker_delete.py`

### 5.3 Mode Toggle Logic

Create logic to toggle FOLLOW ↔ RECORD on GO long press:

1. This is handled by **menu_engine.py** via `/vplayer/mode_toggle` path
2. When `state['mode']` changes, update LED feedback (see Part 7)

---

## Part 6: Marker Lookup (FOLLOW Mode)

### 6.1 Marker Lookup Script

1. Create **Text DAT**
   - Name: `marker_lookup`
2. Copy content from: `vplayer_scripts/marker_lookup.py`

### 6.2 Manual Navigation Buttons (Optional UI)

If creating UI buttons for Next/Previous marker:

1. Create **Button COMP** named `btn_next`
   - Parameter Execute: `op('../marker_lookup').module.jump_to_next_marker()`
2. Create **Button COMP** named `btn_prev`
   - Parameter Execute: `op('../marker_lookup').module.jump_to_previous_marker()`

---

## Part 7: LED Feedback System

### 7.1 LED State Generator

Create CHOPs to generate LED states based on mode and progress:

1. **Constant CHOP** `led_go_state`:
   - Channels: `1`
   - Name: `btn_21_led` (GO button)
   - Expression:
```python
# Get mode and progress
mode = op('state')['mode']
progress = op('eos_state')['progress']

# RECORD mode: Blink handled by driver_led
if mode == 1:
    return 1  # Bright green (blink pattern in driver)

# FOLLOW mode: Idle vs Fahrt
if progress < 0.01 or progress > 0.99:
    return 0.3  # Dark green (idle)
else:
    return 0.8  # Bright green (fahrt)
```

2. **Math CHOP** `led_blink` (for RECORD mode):
   - Pattern: `Square`
   - Frequency: `2` Hz (500ms on/off)
   - Amplitude: `1`

3. **Switch CHOP** (select blink or solid based on mode):
   - Inputs: `led_go_state`, `led_blink`
   - Index: Expression → `int(op('state')['mode'])`

### 7.2 Connect to driver_led.py

*See LED_FEEDBACK_GUIDE.md for full integration.*

Quick integration:
1. Find existing LED constant CHOP (likely at `/project1/io/led_const`)
2. Add channel for `btn/21` with value from your LED state CHOP
3. Use existing `driver_led.py` module to send MIDI LED updates

---

## Part 8: UI Container (Optional but Recommended)

### 8.1 Create Container COMP

1. Create **Container COMP**
   - Name: `container_ui`
2. Inside, create layout with **Panel COMPs**

### 8.2 Status Bar

**Text TOP** for status display:
1. Name: `status_bar`
2. Expression on Text parameter:
```python
mode = 'RECORD' if op('../state')['mode'] == 1 else 'FOLLOW'
active = f"{int(op('../eos_state')['active_list'])}/{int(op('../eos_state')['active_cue'])}"
pending = f"{int(op('../eos_state')['pending_list'])}/{int(op('../eos_state')['pending_cue'])}"
marker_count = max(0, op('../markers').numRows - 1)

return f"[{mode}] Active: {active} | Pending: {pending} | Markers: {marker_count}"
```

### 8.3 Timeline Visualization

Create a custom timeline with marker ticks:

1. **Container COMP** `timeline`:
   - Use **SOP** geometry to draw line and marker ticks
   - **Render TOP** to display
2. Marker positions from `markers` DAT → `pos_s / length_seconds`
3. Playhead position from `info_video['position_seconds'] / length_seconds`

*Full timeline implementation is complex - consider starting with simple text display.*

### 8.4 Control Panel

**Panel COMPs** for UI controls:
- Play/Pause toggle (binds to `moviefilein1.play`)
- Loop toggle (binds to `state['loop']`)
- Speed slider (visual feedback, actual control via Fader 2)
- Volume slider (visual feedback, actual control via Fader 3)
- Manual cue jump text field

---

## Part 9: Testing Checklist

### 9.1 Basic Playback
- [ ] Load video file in `moviefilein1`
- [ ] Video plays and audio outputs
- [ ] **Fader 1** scrubs position (video jumps, keeps playing)
- [ ] **Fader 2** changes speed (0.5x - 2.0x)
- [ ] **Fader 3** changes volume (0 - 100%)

### 9.2 Mode Toggle
- [ ] **GO long press** (~0.7s) toggles FOLLOW ↔ RECORD
- [ ] LED changes: Solid green (FOLLOW) ↔ Blinking green (RECORD)
- [ ] Mode displayed in UI

### 9.3 RECORD Mode
- [ ] In RECORD, GO short press:
  - [ ] Marker created for pending cue at current position
  - [ ] Marker appears in `markers` table
  - [ ] LED flash (green)
- [ ] In RECORD, BACK short press:
  - [ ] Marker for pending cue deleted
  - [ ] LED flash (green)
- [ ] Duplicate GO press: Marker replaced (not duplicated)

### 9.4 FOLLOW Mode
- [ ] Eos GO pressed (active cue changes):
  - [ ] If marker exists: Video jumps to marker position
  - [ ] If no marker: Video continues (no jump)
  - [ ] OSC events logged in textport
- [ ] Eos BACK pressed:
  - [ ] If marker exists: Video jumps to previous cue marker
  - [ ] If no marker: No jump (optional red LED flash)

### 9.5 LED Feedback
- [ ] FOLLOW + Idle (progress <0.01 or >0.99): Dark green LED
- [ ] FOLLOW + Fahrt (0.01 < progress < 0.99): Bright green LED
- [ ] RECORD: Green blinking LED (500ms intervals)
- [ ] Marker set/delete: Brief green flash

### 9.6 OSC Integration
- [ ] `/eos/out/active/cue/<list>/<cue>` triggers video jump (if marker exists)
- [ ] `/eos/out/pending/cue/<list>/<cue>` updates pending display
- [ ] `/eos/out/active/cue` float updates progress for LED

---

## Part 10: Optimization and Tips

### 10.1 Performance
- Use **Null CHOPs** for organization (doesn't affect performance)
- Keep `moviefilein1` codec as **HAP** or **NotchLC** for best performance
- Enable **GPU Direct** in Movie File In if supported

### 10.2 Marker Persistence
Save/load markers between sessions:
```python
# Save
markers = op('/project1/media/vplayer/markers')
markers.save('markers_backup.txt')

# Load
markers.load('markers_backup.txt')
```

Or export as JSON:
1. Create **DAT Execute** on `markers`
2. On `onTableChange`: Export to JSON file
3. Load JSON on startup with Python script

### 10.3 Multiple Videos
To support multiple videos per show:
- Create **Select DAT** to filter markers by video filename
- Store video filename in `state` CHOP
- Prefix marker keys: `video1_1/23`, `video2_1/45`

### 10.4 Backup Strategy
Before rehearsal:
1. Backup `markers` DAT → `project1/media/vplayer/markers_backup_{date}.txt`
2. Save `.toe` file with markers intact
3. Export markers as CSV for spreadsheet editing

---

## Part 11: Troubleshooting

### Video doesn't jump on Eos GO
- ✅ Check OSC In is receiving `/eos/out/active/cue` messages (textport)
- ✅ Verify marker exists in `markers` table for that cue
- ✅ Confirm `mode == 0` (FOLLOW mode)
- ✅ Check `osc_event_handler` DAT has no Python errors

### Faders don't respond
- ✅ Verify Menu 5 is active (`ACTIVE_MENU` storage on project1)
- ✅ Check `map_osc.tsv` has correct mappings
- ✅ Confirm MIDI events reach `bus_events` (check with Monitor CHOP)
- ✅ Verify `menu_engine.py` `_handle_vplayer_command` is called (add print statements)

### Markers not created in RECORD
- ✅ Confirm `mode == 1` (RECORD mode active)
- ✅ Check `eos_state` has valid `pending_list` and `pending_cue` values
- ✅ Verify `marker_write` DAT has no Python errors (check textport)
- ✅ Ensure `markers` table is not locked/read-only

### LED not updating
- ✅ Verify LED state CHOP is connected to `driver_led.py`
- ✅ Check MIDI Out is sending to MIDICRAFT ENC
- ✅ Confirm button 21 MIDI Note is correct (Note 26)
- ✅ Test LED manually: `op('/project1/io/driver_led').module.send_led('btn/21', 'press', 'green')`

### Audio crackling/dropouts
- ✅ Increase audio buffer size in `audiodeviceout1` parameters
- ✅ Check CPU usage (Performance Monitor)
- ✅ Use **NotchLC** or **HAP** codec for lower CPU load
- ✅ Reduce video resolution if performance is critical

---

## Completion

Congratulations! Your video player is now fully integrated with:
- ✅ Passive Eos following (no OSC output)
- ✅ Marker-based cue synchronization
- ✅ FOLLOW/RECORD mode system
- ✅ Hardware fader control (scrub/speed/volume)
- ✅ LED feedback for mode and cue state

**Next Steps:**
1. Load your show video files
2. Run through rehearsal in RECORD mode to create markers
3. Switch to FOLLOW mode for performance
4. Adjust LED timing/colors as needed (see LED_FEEDBACK_GUIDE.md)

**Files Created:**
- [menus/menu_5/map_osc.tsv](menus/menu_5/map_osc.tsv) - Updated MIDI mappings
- [menus/menu_engine.py](menus/menu_engine.py) - Event handler added
- `vplayer_scripts/*.py` - Marker management scripts
- TouchDesigner component: `/project1/media/vplayer` (built by you)

---

**Support & References:**
- OSC Configuration: [OSC_IN_GUIDE.md](OSC_IN_GUIDE.md)
- LED Integration: [LED_FEEDBACK_GUIDE.md](LED_FEEDBACK_GUIDE.md)
- Architecture Overview: See original planning document

**Author:** Claude Code Agent
**Version:** 1.0
**Date:** 2025-01-14
