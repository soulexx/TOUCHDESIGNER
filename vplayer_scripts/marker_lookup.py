"""
Marker Lookup and Navigation Scripts for Video Player
Provides functions for manual marker navigation and lookup

Usage in TouchDesigner:
- Create Script DAT
- Call functions from UI buttons or other DATs
"""

def jump_to_marker(marker_key):
    """
    Jump video to specific marker by key

    Args:
        marker_key: Marker key string (e.g. "1/23")

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            print("[marker_lookup] ERROR: vplayer component not found")
            return False

        markers = vplayer.op('markers')
        moviefile = vplayer.op('moviefilein1')

        if not markers or not moviefile:
            print("[marker_lookup] ERROR: Required components missing")
            return False

        # Find marker
        row_index = markers.findCell(marker_key, cols=['key'])

        if row_index is not None:
            pos_s = float(markers[row_index, 'pos_s'])
            moviefile.par.cuepointseconds = pos_s
            moviefile.par.cue.pulse()
            print(f"[marker_lookup] JUMP: {marker_key} -> {pos_s:.2f}s")
            return True
        else:
            print(f"[marker_lookup] Marker not found: {marker_key}")
            return False

    except Exception as exc:
        print(f"[marker_lookup] EXCEPTION: {exc}")
        import traceback
        traceback.print_exc()
        return False


def jump_to_next_marker():
    """
    Jump to next marker after current video position

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            return False

        markers = vplayer.op('markers')
        info_video = vplayer.op('info_video')
        moviefile = vplayer.op('moviefilein1')

        if not all([markers, info_video, moviefile]):
            return False

        # Get current position
        current_pos = float(info_video['position_seconds'].eval())

        # Find next marker (pos_s > current_pos)
        next_marker = None
        next_pos = float('inf')

        for row in range(markers.numRows):
            if row == 0:  # Skip header
                continue
            try:
                pos_s = float(markers[row, 'pos_s'])
                if pos_s > current_pos and pos_s < next_pos:
                    next_pos = pos_s
                    next_marker = markers[row, 'key']
            except Exception:
                continue

        if next_marker:
            moviefile.par.cuepointseconds = next_pos
            moviefile.par.cue.pulse()
            print(f"[marker_lookup] NEXT: {next_marker} -> {next_pos:.2f}s")
            return True
        else:
            print("[marker_lookup] No next marker found")
            return False

    except Exception as exc:
        print(f"[marker_lookup] EXCEPTION in jump_to_next_marker: {exc}")
        return False


def jump_to_previous_marker():
    """
    Jump to previous marker before current video position

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            return False

        markers = vplayer.op('markers')
        info_video = vplayer.op('info_video')
        moviefile = vplayer.op('moviefilein1')

        if not all([markers, info_video, moviefile]):
            return False

        # Get current position
        current_pos = float(info_video['position_seconds'].eval())

        # Find previous marker (pos_s < current_pos)
        prev_marker = None
        prev_pos = float('-inf')

        for row in range(markers.numRows):
            if row == 0:  # Skip header
                continue
            try:
                pos_s = float(markers[row, 'pos_s'])
                if pos_s < current_pos and pos_s > prev_pos:
                    prev_pos = pos_s
                    prev_marker = markers[row, 'key']
            except Exception:
                continue

        if prev_marker:
            moviefile.par.cuepointseconds = prev_pos
            moviefile.par.cue.pulse()
            print(f"[marker_lookup] PREV: {prev_marker} -> {prev_pos:.2f}s")
            return True
        else:
            print("[marker_lookup] No previous marker found")
            return False

    except Exception as exc:
        print(f"[marker_lookup] EXCEPTION in jump_to_previous_marker: {exc}")
        return False


def get_marker_count():
    """
    Get total number of markers

    Returns:
        int: Number of markers (excluding header row)
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            return 0

        markers = vplayer.op('markers')
        if not markers:
            return 0

        # Subtract 1 for header row
        return max(0, markers.numRows - 1)

    except Exception:
        return 0


def get_nearest_marker_info():
    """
    Get info about nearest marker to current position

    Returns:
        dict: {'key': str, 'pos_s': float, 'label': str} or None
    """
    try:
        vplayer = op('/project1/media/vplayer')
        if not vplayer:
            return None

        markers = vplayer.op('markers')
        info_video = vplayer.op('info_video')

        if not markers or not info_video:
            return None

        current_pos = float(info_video['position_seconds'].eval())

        # Find closest marker (any direction)
        nearest_marker = None
        nearest_distance = float('inf')

        for row in range(markers.numRows):
            if row == 0:  # Skip header
                continue
            try:
                pos_s = float(markers[row, 'pos_s'])
                distance = abs(pos_s - current_pos)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_marker = {
                        'key': markers[row, 'key'].val,
                        'pos_s': pos_s,
                        'label': markers[row, 'label'].val
                    }
            except Exception:
                continue

        return nearest_marker

    except Exception as exc:
        print(f"[marker_lookup] EXCEPTION in get_nearest_marker_info: {exc}")
        return None


# Example UI button callbacks
def on_next_button():
    """UI callback for Next Marker button"""
    jump_to_next_marker()


def on_prev_button():
    """UI callback for Previous Marker button"""
    jump_to_previous_marker()


def on_jump_to_cue(cue_input):
    """
    UI callback for manual cue jump

    Args:
        cue_input: String like "1/23" or Panel value
    """
    try:
        # Handle Panel object
        if hasattr(cue_input, 'val'):
            cue_key = cue_input.val
        else:
            cue_key = str(cue_input)

        jump_to_marker(cue_key.strip())

    except Exception as exc:
        print(f"[marker_lookup] Invalid cue input: {exc}")
