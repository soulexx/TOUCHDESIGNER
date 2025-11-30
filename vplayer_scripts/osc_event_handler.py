"""
OSC Event Handler for Video Player (FOLLOW Mode)
Processes Eos OSC feedback and triggers video jumps

Handles:
- /eos/out/active/cue/<list>/<cue> → Jump to marker if exists
- /eos/out/pending/cue/<list>/<cue> → Update pending cue info
- /eos/out/active/cue (Float) → Update progress for LED
- /eos/out/previous/cue/<list>/<cue> → Jump to previous marker (BACK)

Usage in TouchDesigner:
- Create Script DAT
- Trigger from OSC In MAP or OSC In DAT callbacks
"""

def on_active_cue_change(cue_list, cue_number):
    """
    Called when Eos active cue changes (GO button pressed)
    Jumps video to marker if exists

    Args:
        cue_list: Cue list number (int)
        cue_number: Cue number (int or float)
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            return

        # Check mode (must be FOLLOW = 0)
        state = vplayer.op('state')
        if not state or state['mode'].eval() != 0:
            return  # Ignore in RECORD mode

        # Build key (list/cue format, no parts)
        key = f"{int(cue_list)}/{int(cue_number)}"

        # Update eos_state for display
        eos_state = vplayer.op('eos_state')
        if eos_state:
            eos_state['active_list'] = cue_list
            eos_state['active_cue'] = cue_number

        # Lookup marker
        markers = vplayer.op('markers')
        if not markers:
            return

        row_index = markers.findCell(key, cols=['key'])

        if row_index is not None:
            # Marker found - jump video
            pos_s = float(markers[row_index, 'pos_s'])
            moviefile = vplayer.op('moviefilein1')

            if moviefile:
                moviefile.par.cuepointseconds = pos_s
                moviefile.par.cue.pulse()
                print(f"[eos_event] JUMP: {key} -> {pos_s:.2f}s")
            else:
                print(f"[eos_event] ERROR: moviefilein1 not found")
        else:
            # No marker - video continues playing
            print(f"[eos_event] No marker for {key}, continuing playback")

    except Exception as exc:
        print(f"[eos_event] EXCEPTION in on_active_cue_change: {exc}")
        import traceback
        traceback.print_exc()


def on_pending_cue_change(cue_list, cue_number):
    """
    Called when Eos pending cue changes
    Updates pending cue info for RECORD mode

    Args:
        cue_list: Cue list number (int)
        cue_number: Cue number (int or float)
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            return

        eos_state = vplayer.op('eos_state')
        if not eos_state:
            return

        # Update pending cue info
        eos_state['pending_list'] = cue_list
        eos_state['pending_cue'] = cue_number

        key = f"{int(cue_list)}/{int(cue_number)}"
        print(f"[eos_event] Pending: {key}")

    except Exception as exc:
        print(f"[eos_event] EXCEPTION in on_pending_cue_change: {exc}")


def on_progress_update(progress_value):
    """
    Called when Eos active cue progress changes (0.0-1.0)
    Used for LED Idle/Fahrt detection

    Args:
        progress_value: Float 0.0 to 1.0
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            return

        eos_state = vplayer.op('eos_state')
        if eos_state:
            eos_state['progress'] = float(progress_value)

    except Exception as exc:
        print(f"[eos_event] EXCEPTION in on_progress_update: {exc}")


def on_previous_cue(cue_list, cue_number):
    """
    Called when Eos BACK is pressed (previous cue)
    Jumps video to marker if exists

    Args:
        cue_list: Cue list number (int)
        cue_number: Cue number (int or float)
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            return

        # Check mode (must be FOLLOW = 0)
        state = vplayer.op('state')
        if not state or state['mode'].eval() != 0:
            return  # Ignore in RECORD mode

        # Build key
        key = f"{int(cue_list)}/{int(cue_number)}"

        # Lookup marker
        markers = vplayer.op('markers')
        if not markers:
            return

        row_index = markers.findCell(key, cols=['key'])

        if row_index is not None:
            # Marker found - jump video
            pos_s = float(markers[row_index, 'pos_s'])
            moviefile = vplayer.op('moviefilein1')

            if moviefile:
                moviefile.par.cuepointseconds = pos_s
                moviefile.par.cue.pulse()
                print(f"[eos_event] BACK JUMP: {key} -> {pos_s:.2f}s")
        else:
            # No marker - show error LED flash
            print(f"[eos_event] No marker for {key} on BACK")
            led_flash = vplayer.op('led_flash_error')
            if led_flash:
                led_flash.par.value0 = 1  # Red flash

    except Exception as exc:
        print(f"[eos_event] EXCEPTION in on_previous_cue: {exc}")
        import traceback
        traceback.print_exc()


# Example OSC In MAP callback integration
def on_osc_message(address, *args):
    """
    Universal OSC callback handler
    Can be used with OSC In DAT's onReceiveOSC callback

    Args:
        address: OSC address string
        *args: OSC arguments
    """
    try:
        if '/eos/out/active/cue' in address and len(args) >= 2:
            # /eos/out/active/cue/<list>/<cue>
            parts = address.split('/')
            if len(parts) >= 6:
                cue_list = int(parts[4])
                cue_number = int(parts[5])
                on_active_cue_change(cue_list, cue_number)

        elif '/eos/out/pending/cue' in address and len(args) >= 2:
            # /eos/out/pending/cue/<list>/<cue>
            parts = address.split('/')
            if len(parts) >= 6:
                cue_list = int(parts[4])
                cue_number = int(parts[5])
                on_pending_cue_change(cue_list, cue_number)

        elif address == '/eos/out/active/cue' and len(args) == 1:
            # Progress float
            progress = float(args[0])
            on_progress_update(progress)

        elif '/eos/out/previous/cue' in address and len(args) >= 2:
            # /eos/out/previous/cue/<list>/<cue>
            parts = address.split('/')
            if len(parts) >= 6:
                cue_list = int(parts[4])
                cue_number = int(parts[5])
                on_previous_cue(cue_list, cue_number)

    except Exception as exc:
        print(f"[eos_event] EXCEPTION in on_osc_message: {exc}")
