"""
Marker Delete Script for Video Player (RECORD Mode)
Triggered by BACK button (short press) in RECORD mode
Deletes marker for the pending cue (undo last marker set)

Usage in TouchDesigner:
- Create Script DAT
- Copy this code
- Trigger with CHOP Execute or Button parameter execute
"""

def delete_marker():
    """Delete marker for pending cue"""
    try:
        # Get components
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            print("[marker_delete] ERROR: vplayer component not found")
            return False

        # Get state
        state = vplayer.op('state')
        eos_state = vplayer.op('eos_state')
        markers = vplayer.op('markers')

        if not all([state, eos_state, markers]):
            print("[marker_delete] ERROR: Required components missing")
            return False

        # Check mode (must be RECORD = 1)
        mode = state['mode'].eval()
        if mode != 1:
            print("[marker_delete] Not in RECORD mode, ignoring")
            return False

        # Get pending cue key
        try:
            pending_list = int(eos_state['pending_list'].eval())
            pending_cue = int(eos_state['pending_cue'].eval())
            key = f"{pending_list}/{pending_cue}"
        except Exception as exc:
            print(f"[marker_delete] ERROR: Invalid pending cue data: {exc}")
            return False

        # Find marker
        row_index = markers.findCell(key, cols=['key'])

        if row_index is not None:
            # Delete marker
            markers.deleteRow(row_index)
            print(f"[marker_delete] DELETED: {key}")

            # Trigger LED flash (optional - connect to LED system)
            led_flash = vplayer.op('led_flash')
            if led_flash:
                led_flash.par.value0 = 1  # Bright green flash

            return True
        else:
            print(f"[marker_delete] No marker found for {key}")
            return False

    except Exception as exc:
        print(f"[marker_delete] EXCEPTION: {exc}")
        import traceback
        traceback.print_exc()
        return False


# Entry point for Script DAT execution
if __name__ == '__main__':
    delete_marker()
