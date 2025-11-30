# LED Feedback Integration Guide - MIDICRAFT ENC LEDs

Complete guide for integrating video player state into MIDICRAFT ENC hardware LED feedback system.

## Overview

The video player uses hardware LEDs to communicate state:

**GO Button (Button 21, MIDI Note 26):**
- **FOLLOW Mode + Idle**: Dark green (solid)
- **FOLLOW Mode + Fahrt**: Bright green (solid) - cue is running (0 < progress < 1)
- **RECORD Mode**: Green blinking (500ms intervals, green ↔ black)

**Optional Feedback:**
- **Marker Set**: Brief bright green flash (200ms)
- **Marker Deleted**: Brief bright green flash (200ms)
- **Error** (no marker on BACK): Brief bright red flash (200ms)

---

## Part 1: Understanding Existing LED System

### 1.1 Current LED Architecture

Your project already has LED feedback via `driver_led.py`:

**Component Locations:**
- **driver_led.py**: `/project1/io/driver_led.py` (or similar path)
- **led_const**: Constant CHOP with LED states (one channel per button)
- **MIDI Out**: Sends Note On/Off messages to MIDICRAFT ENC

**Existing Pattern (from your system):**
```python
# driver_led.py pattern
def send_led(topic, state, color, do_send=True):
    """
    topic: 'btn/21'
    state: 'press', 'idle', 'blink'
    color: 'green', 'red', 'yellow', etc.
    """
    # Maps color+state to MIDI velocity value
    # Sends MIDI Note On to hardware
```

**Velocity Palette (typical):**
- Off: `0`
- Dark color: `10-30`
- Bright color: `80-127`
- Blink: Alternating values via timer

### 1.2 Current Menu 5 LED Usage

Check existing LED state for Button 21:

1. Navigate to LED Constant CHOP (likely `/project1/io/led_const`)
2. Look for channel `btn/21` or `btn_21`
3. Current value is likely:
   - `0` (off)
   - Or controlled by Eos GO button state

**Conflict Check:**
- If Button 21 LED is already in use by Eos control, we'll **override** it with video player state
- In Menu 5 (video player active), video state takes priority
- In other menus, Eos control resumes

---

## Part 2: LED State Generator (CHOP Network)

### 2.1 Create LED State Logic in vplayer

Inside `/project1/media/vplayer`, create CHOP network:

**Step 1: Mode-Based State**

1. **Math CHOP** `led_mode_check`:
   - Input: `state` (mode channel)
   - Operation: `Compare`
   - Compare To: `1` (RECORD mode)
   - Output: `1` if RECORD, `0` if FOLLOW

2. **Math CHOP** `led_progress_check`:
   - Input: `eos_state` (progress channel)
   - Operation: Two instances:
     - `led_progress_idle`: `progress < 0.01 OR progress > 0.99` → `1` (Idle)
     - `led_progress_fahrt`: `0.01 <= progress <= 0.99` → `1` (Fahrt)

**Step 2: LED Value Assignment**

Create **Constant CHOP** `led_values` with channels:
- `dark_green`: Value `20` (FOLLOW Idle)
- `bright_green`: Value `100` (FOLLOW Fahrt)
- `blink_green`: Value `100` (RECORD, will be modulated)
- `off`: Value `0` (for blink off-state)

**Step 3: Blink Generator**

1. **LFO CHOP** `led_blink_lfo`:
   - Type: `Square`
   - Frequency: `2` Hz (500ms period)
   - Amplitude: `1`
   - Offset: `0`
   - Range: `0` to `1`

2. **Math CHOP** `led_blink_switch`:
   - Input 0: `led_blink_lfo`
   - Operation: `Threshold`
   - Threshold: `0.5`
   - Output: `1` (on) or `0` (off) alternating

**Step 4: State Selector**

Create **Logic CHOP** `led_state_select`:

```python
# Expression in Logic CHOP or Script CHOP
mode = op('state')['mode']
progress = op('eos_state')['progress']
blink = op('led_blink_switch')[0]

if mode == 1:  # RECORD
    # Blink green ↔ black
    return op('led_values')['blink_green'] if blink else 0
else:  # FOLLOW
    if progress < 0.01 or progress > 0.99:
        # Idle: Dark green
        return op('led_values')['dark_green']
    else:
        # Fahrt: Bright green
        return op('led_values')['bright_green']
```

**Or use Switch CHOP chain:**
1. **Switch CHOP** `mode_switch`:
   - Input 0: FOLLOW state (from next switch)
   - Input 1: RECORD blink value
   - Index: `op('state')['mode']`

2. **Switch CHOP** `progress_switch` (FOLLOW sub-switch):
   - Input 0: `dark_green` (Idle)
   - Input 1: `bright_green` (Fahrt)
   - Index: `led_progress_fahrt[0]` (1 if Fahrt, 0 if Idle)

### 2.2 Final LED Output

**Constant CHOP** `led_go_out`:
- Channel: `btn_21`
- Value: Expression → `op('led_state_select')[0]`

This is the final LED value for GO button, ready to send to `driver_led`.

---

## Part 3: Integration with driver_led.py

### 3.1 Locate LED Constant CHOP

Find the main LED state CHOP (likely `/project1/io/led_const`):

1. This CHOP aggregates all LED states from different sources
2. It has channels like: `btn_11`, `btn_21`, `enc_push_1`, etc.
3. Values are MIDI velocities (0-127)

### 3.2 Add Video Player LED Channel

**Option A: Direct Channel Addition**

1. In `led_const` Constant CHOP:
   - Increase "Channels" parameter by 1
   - Name new channel: `btn_21_vplayer`
   - Value: Expression → `op('/project1/media/vplayer/led_go_out')['btn_21']`

2. Create **Merge CHOP** to combine with existing `btn_21`:
   - Input 0: Existing `btn_21` (from Eos/Menu system)
   - Input 1: `btn_21_vplayer` (from video player)
   - Operation: Menu-based priority:
     ```python
     # If Menu 5 active, use vplayer LED; else use Eos LED
     active_menu = op('/project1').fetch('ACTIVE_MENU', 0)
     if active_menu == 5:
         return op('led_const')['btn_21_vplayer']
     else:
         return op('led_const')['btn_21']  # Original Eos LED
     ```

**Option B: Conditional Override**

Modify existing `btn_21` channel expression in `led_const`:

```python
# Check if Menu 5 is active
active_menu = op('/project1').fetch('ACTIVE_MENU', 0)

if active_menu == 5:
    # Use video player LED state
    vplayer = op('/project1/media/vplayer')
    if vplayer:
        led_out = vplayer.op('led_go_out')
        if led_out and led_out.numChans > 0:
            return led_out['btn_21'].eval()

# Fallback to Eos control (original logic)
return ... (existing expression)
```

### 3.3 Test LED Output

**Manual Test:**
1. In vplayer, manually set mode:
   ```python
   op('state')['mode'] = 1  # RECORD → Should blink green
   op('state')['mode'] = 0  # FOLLOW → Should be dark/bright green
   ```

2. Set progress:
   ```python
   op('eos_state')['progress'] = 0.5  # Fahrt → Bright green
   op('eos_state')['progress'] = 0.0  # Idle → Dark green
   ```

3. Check `led_const` channel `btn_21`:
   - Value should change accordingly
   - RECORD: Alternating ~100 ↔ 0 (2 Hz)
   - FOLLOW Idle: ~20
   - FOLLOW Fahrt: ~100

4. Observe hardware LED on MIDICRAFT ENC:
   - Should visually match the state

**If hardware LED doesn't update:**
- Check MIDI Out is active (look for "MIDICRAFT ENC" device)
- Verify `driver_led.py` is being called (add print statements)
- Check MIDI channel matches hardware (usually channel 1)

---

## Part 4: Flash Feedback (Optional)

### 4.1 Marker Set/Delete Flash

Add brief LED flash when marker is created/deleted:

1. **Timer CHOP** `led_flash_timer`:
   - Length: `0.2` seconds
   - Trigger: Manual (via Python pulse)

2. **Math CHOP** `led_flash_value`:
   - Input: `led_flash_timer`
   - Operation: Threshold
   - Threshold: `0.01` (on during timer active)
   - Output Value: `120` (bright green flash)

3. **Add to LED Chain:**

   Modify LED state selector to include flash:
   ```python
   base_value = op('led_state_select')[0]  # Normal state
   flash_value = op('led_flash_value')[0]  # Flash overlay

   return max(base_value, flash_value)  # Flash overrides normal
   ```

4. **Trigger from marker_write.py:**

   In `marker_write.py`, after marker set:
   ```python
   # Trigger LED flash
   led_flash = vplayer.op('led_flash_timer')
   if led_flash:
       led_flash.par.initialize.pulse()
   ```

### 4.2 Error Flash (No Marker on BACK)

Create separate red flash for errors:

1. **Timer CHOP** `led_flash_error`:
   - Length: `0.2` seconds

2. **Constant CHOP** `led_error_value`:
   - Channel: `btn_11` (BACK button)
   - Value: `127` (bright red)

3. **Trigger from osc_event_handler.py:**

   In `on_previous_cue()`, when no marker found:
   ```python
   if row_index is None:
       # No marker - flash red
       led_flash = vplayer.op('led_flash_error')
       if led_flash:
           led_flash.par.initialize.pulse()
   ```

4. **Integrate with btn_11 LED:**
   - Similar to GO button, merge error flash with normal BACK LED state

---

## Part 5: Advanced LED Patterns

### 5.1 Smooth Fade (Instead of Instant Switch)

Add **Filter CHOP** for smoother LED transitions:

1. **Filter CHOP** `led_smooth`:
   - Input: `led_state_select`
   - Filter Type: `Lag`
   - Lag: `0.1` (100ms fade)

This creates smooth fade between dark ↔ bright green (less jarring).

### 5.2 Progress-Based Brightness

Map cue progress (0-1) directly to LED brightness:

```python
# Instead of binary Idle/Fahrt, use gradient
mode = op('state')['mode']
progress = op('eos_state')['progress']

if mode == 1:  # RECORD
    return blink_value  # (unchanged)
else:  # FOLLOW
    # Map progress 0-1 to brightness 20-100
    min_brightness = 20   # Idle (dark green)
    max_brightness = 100  # Full Fahrt (bright green)

    # Clamp progress to 0-1
    progress_clamped = max(0, min(1, progress))

    # Linear interpolation
    brightness = min_brightness + (max_brightness - min_brightness) * progress_clamped

    return brightness
```

This gives **continuous feedback** of fade progress (dimmer → brighter as cue progresses).

### 5.3 Multi-Color States

If MIDICRAFT ENC supports RGB LEDs or velocity-based colors:

**Color Palette:**
- Dark Green: Velocity `20-30`
- Bright Green: Velocity `80-100`
- Yellow: Velocity `40-50` (optional "pending" state)
- Red: Velocity `60-70` (error flash)

Modify LED logic to output different velocities based on state.

---

## Part 6: Debugging LED Issues

### 6.1 LED Not Changing

**Checklist:**
- [ ] `led_go_out` CHOP has correct value (check with Info CHOP)
- [ ] `led_const` channel `btn_21` updates (watch in parameter viewer)
- [ ] MIDI Out is active and sending (check MIDI Monitor or Eos console feedback)
- [ ] MIDICRAFT ENC is receiving MIDI (check device LEDs flash on other buttons)
- [ ] Correct MIDI channel (usually 1)
- [ ] Correct MIDI note number (Button 21 = Note 26)

**Debug Steps:**
1. Create **MIDI Out CHOP**:
   - Input: `led_const` channel `btn_21`
   - Channel Name: `note26` (or appropriate for Note On 26)
   - Network: MIDICRAFT ENC device

2. Create **MIDI Event DAT**:
   - Connect to MIDI Out
   - Watch for Note On messages in real-time

3. If messages sent but LED not responding:
   - Check hardware MIDI input settings
   - Verify Note 26 is mapped to Button 21 LED (not just button press)
   - Try different velocity values (some LEDs only respond to specific ranges)

### 6.2 Blink Rate Wrong

If blink is too fast/slow:

**Adjust LFO Frequency:**
- Current: `2` Hz (500ms period, 250ms on + 250ms off)
- Faster: `4` Hz (125ms on + 125ms off)
- Slower: `1` Hz (500ms on + 500ms off)

**Match Project Style:**
- Check existing blink patterns in your project (Menu 0 submenu blinks)
- Use same blink manager if available:
  ```python
  # If project has global blink manager
  blink_mgr = op('/project1/io/blink_manager')  # (example path)
  if blink_mgr:
      blink_value = blink_mgr['blink_green']
  ```

### 6.3 LED Flash Not Visible

If flash is too brief:

**Increase Timer Length:**
- Change `led_flash_timer` length from `0.2` to `0.5` seconds

**Use Pulse CHOP Instead:**
1. **Pulse CHOP** `led_flash_pulse`:
   - Pulse Length: `10` samples (~150ms at 60fps)
   - Amplitude: `120`

2. Trigger via:
   ```python
   op('led_flash_pulse').par.sendpulse.pulse()
   ```

---

## Part 7: Integration Checklist

Verify LED feedback is working correctly:

### 7.1 FOLLOW Mode Tests

- [ ] **Idle State** (no cue running):
  - Progress = 0.0 or 1.0
  - GO LED is **dark green** (velocity ~20-30)

- [ ] **Fahrt State** (cue fading):
  - Progress = 0.3 (mid-fade)
  - GO LED is **bright green** (velocity ~80-100)

- [ ] **Transition**:
  - Press GO on Eos
  - LED should change dark → bright → dark over fade time

### 7.2 RECORD Mode Tests

- [ ] **Enter RECORD**:
  - Long press GO (~0.7s)
  - LED should start **blinking** green ↔ black at ~2 Hz

- [ ] **Exit RECORD**:
  - Long press GO again
  - LED should stop blinking, return to solid (dark/bright green)

### 7.3 Flash Tests

- [ ] **Marker Set**:
  - In RECORD, press GO short
  - LED should **flash bright green** briefly (~200ms)

- [ ] **Marker Delete**:
  - In RECORD, press BACK short
  - LED should **flash bright green** briefly

- [ ] **Error Flash** (optional):
  - In FOLLOW, press BACK when no marker exists
  - BACK button LED should **flash red** briefly

### 7.4 Menu Switching

- [ ] Switch to Menu 0 (or other menu)
  - GO LED should revert to Eos control (green when ready)

- [ ] Switch back to Menu 5
  - GO LED should immediately show video player state (dark/bright/blink)

---

## Part 8: Performance Optimization

### 8.1 Reduce CHOP Cooking

LED updates don't need 60fps:

1. **Set CHOP Cook Type**:
   - Right-click `led_state_select` → "Cooking" → "Rate" → `30 FPS`
   - Or use Time Slicing: `Every 2nd Frame`

2. **Use Lag CHOP**:
   - Smooth value changes reduce MIDI message spam
   - Lag time `0.05` - `0.1` seconds is sufficient

### 8.2 Debounce Flash Triggers

Prevent multiple flash triggers in quick succession:

```python
# In marker_write.py
import time

last_flash_time = getattr(parent(), 'last_flash_time', 0)
current_time = time.time()

if current_time - last_flash_time > 0.5:  # Min 500ms between flashes
    led_flash.par.initialize.pulse()
    parent().last_flash_time = current_time
```

---

## Part 9: Custom LED Patterns (Advanced)

### 9.1 Pulse on Marker Proximity

LED pulses faster as playhead approaches marker:

```python
# Get nearest marker distance
nearest = op('/project1/media/vplayer/marker_lookup').module.get_nearest_marker_info()

if nearest:
    current_pos = op('info_video')['position_seconds']
    marker_pos = nearest['pos_s']
    distance = abs(marker_pos - current_pos)

    # Pulse faster when close (0-5 seconds away)
    if distance < 5:
        pulse_freq = 2 + (5 - distance)  # 2-7 Hz
        op('led_blink_lfo').par.freq = pulse_freq
```

### 9.2 Color-Coded Markers

If using different marker types (e.g., verse/chorus/bridge):

1. Add `type` column to markers table
2. Map marker type to LED color:
   - Verse: Green
   - Chorus: Yellow
   - Bridge: Blue

3. Update LED logic to use marker type of nearest/active marker

### 9.3 Rainbow Progress

Cycle through colors during fade:

```python
progress = op('eos_state')['progress']

# Map progress 0-1 to hue 0-360
hue = progress * 360

# Convert HSV to RGB to MIDI velocity (requires color conversion)
# Or use discrete color steps:
if progress < 0.25:
    color = 'green'
elif progress < 0.5:
    color = 'yellow'
elif progress < 0.75:
    color = 'orange'
else:
    color = 'red'
```

---

## Completion

LED feedback is now fully integrated:

- ✅ GO button shows FOLLOW (dark/bright green) or RECORD (blinking)
- ✅ LED brightness reflects cue progress (Idle/Fahrt)
- ✅ Flash feedback on marker set/delete
- ✅ Menu-aware LED switching (video player in Menu 5 only)

**Result:** Clear hardware feedback of video player state without looking at screen!

**Files Modified:**
- `/project1/media/vplayer/*` - LED state CHOPs added
- `/project1/io/led_const` - Button 21 channel updated (optional)
- `vplayer_scripts/*.py` - Flash trigger calls added

**Performance:** LED updates at 30 FPS, negligible CPU impact.

---

**Author:** Claude Code Agent
**Version:** 1.0
**Date:** 2025-01-14
