"""
Marker Write Script for Video Player (RECORD Mode)
Triggered by GO button (short press) in RECORD mode
Sets or replaces marker for the pending cue at current video position

Usage in TouchDesigner:
- Create Script DAT
- Copy this code
- Trigger with CHOP Execute or Button parameter execute
"""

def write_marker():
    """Write/replace marker for pending cue at current video position"""
    try:
        # Get components
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            print("[marker_write] ERROR: vplayer component not found")
            return False

        # Get state
        state = vplayer.op('state')
        eos_state = vplayer.op('eos_state')
        info_video = vplayer.op('info_video')
        markers = vplayer.op('markers')

        if not all([state, eos_state, info_video, markers]):
            print("[marker_write] ERROR: Required components missing")
            return False

        # Check mode (must be RECORD = 1)
        mode = state['mode'].eval()
        if mode != 1:
            print("[marker_write] Not in RECORD mode, ignoring")
            return False

        # Get pending cue key
        try:
            pending_list = int(eos_state['pending_list'].eval())
            pending_cue = int(eos_state['pending_cue'].eval())
            key = f"{pending_list}/{pending_cue}"
        except Exception as exc:
            print(f"[marker_write] ERROR: Invalid pending cue data: {exc}")
            return False

        # Get current video position
        try:
            pos_s = float(info_video['position_seconds'].eval())
        except Exception as exc:
            print(f"[marker_write] ERROR: Cannot read position: {exc}")
            return False

        # Create label
        label = f"Cue {key}"

        # Check if marker exists
        row_index = markers.findCell(key, cols=['key'])

        if row_index is not None:
            # Replace existing marker
            markers[row_index, 'pos_s'] = pos_s
            print(f"[marker_write] REPLACED: {key} -> {pos_s:.2f}s")
        else:
            # Append new marker
            markers.appendRow([key, pos_s, label])
            print(f"[marker_write] CREATED: {key} -> {pos_s:.2f}s")

        # Trigger LED flash (optional - connect to LED system)
        led_flash = vplayer.op('led_flash')
        if led_flash:
            led_flash.par.value0 = 1  # Bright green flash

        return True

    except Exception as exc:
        print(f"[marker_write] EXCEPTION: {exc}")
        import traceback
        traceback.print_exc()
        return False


# Entry point for Script DAT execution
if __name__ == '__main__':
    write_marker()
