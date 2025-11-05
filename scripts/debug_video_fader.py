"""Debug script for video fader scrubbing issues.

Run this from the Textport to diagnose the video scrubbing problem:

    import scripts.debug_video_fader
    scripts.debug_video_fader.start_monitoring()

    # Move fader 1 on menu 5, then stop monitoring:
    scripts.debug_video_fader.stop_monitoring()
"""

import time

_monitoring = False
_original_handle_event = None
_event_log = []
_max_events = 50


def _wrap_handle_event(original_func):
    """Wrap the handle_event function to log fader events."""
    def wrapper(topic, value):
        if _monitoring and topic and str(topic).startswith('fader/1'):
            timestamp = time.time()
            _event_log.append({
                'time': timestamp,
                'topic': str(topic),
                'value': float(value) if value is not None else None
            })
            if len(_event_log) > _max_events:
                _event_log.pop(0)
        return original_func(topic, value)
    return wrapper


def start_monitoring():
    """Start monitoring fader/1 events."""
    global _monitoring, _original_handle_event

    try:
        eng = op('/project1/layers/menus/menu_engine')
        if not eng:
            print("[debug] ERROR: menu_engine not found")
            return

        module = eng.module
        if not hasattr(module, 'handle_event'):
            print("[debug] ERROR: handle_event not found")
            return

        if _original_handle_event is None:
            _original_handle_event = module.handle_event
            module.handle_event = _wrap_handle_event(_original_handle_event)

        _event_log.clear()
        _monitoring = True
        print("[debug] Monitoring started. Move fader/1 on menu 5, then call stop_monitoring()")

    except Exception as e:
        print(f"[debug] ERROR starting monitor: {e}")
        import traceback
        traceback.print_exc()


def stop_monitoring():
    """Stop monitoring and show results."""
    global _monitoring
    _monitoring = False

    print(f"\n[debug] Captured {len(_event_log)} events:")

    if not _event_log:
        print("[debug] No events captured. Make sure you're on menu 5 and moving fader 1")
        return

    # Analyze the events
    print("\n[debug] First 10 events:")
    for i, evt in enumerate(_event_log[:10]):
        dt = evt['time'] - _event_log[0]['time'] if i > 0 else 0
        print(f"  {i:3d}. {evt['topic']:15s} value={evt['value']:.6f} dt={dt*1000:.1f}ms")

    if len(_event_log) > 10:
        print(f"\n[debug] ... ({len(_event_log) - 10} more events)")

    # Check for value changes
    values = [evt['value'] for evt in _event_log]
    unique_values = len(set(values))
    min_val = min(values)
    max_val = max(values)

    print(f"\n[debug] Value statistics:")
    print(f"  - Unique values: {unique_values}")
    print(f"  - Range: {min_val:.6f} to {max_val:.6f}")
    print(f"  - Value span: {max_val - min_val:.6f}")

    # Calculate frame precision
    try:
        import video_control
        vc = video_control.get_controller()
        info = vc.info()
        if info.total_frames:
            min_frame = int(min_val * (info.total_frames - 1))
            max_frame = int(max_val * (info.total_frames - 1))
            print(f"  - Frame range: {min_frame} to {max_frame} (out of {info.total_frames})")

            # Check smallest value change
            if len(values) > 1:
                diffs = [abs(values[i] - values[i-1]) for i in range(1, len(values)) if values[i] != values[i-1]]
                if diffs:
                    min_diff = min(diffs)
                    frame_step = min_diff * (info.total_frames - 1)
                    print(f"  - Smallest value change: {min_diff:.6f} (~{frame_step:.1f} frames)")
    except Exception as e:
        print(f"  - Could not get video info: {e}")

    # Check timing
    if len(_event_log) > 1:
        times = [evt['time'] for evt in _event_log]
        dts = [(times[i] - times[i-1]) * 1000 for i in range(1, len(times))]
        avg_dt = sum(dts) / len(dts)
        min_dt = min(dts)
        max_dt = max(dts)
        print(f"\n[debug] Timing:")
        print(f"  - Average interval: {avg_dt:.1f}ms")
        print(f"  - Min interval: {min_dt:.1f}ms")
        print(f"  - Max interval: {max_dt:.1f}ms")
        print(f"  - Event rate: {1000/avg_dt:.1f} events/second")


def reset():
    """Reset the monitoring system."""
    global _monitoring, _original_handle_event

    try:
        if _original_handle_event is not None:
            eng = op('/project1/layers/menus/menu_engine')
            if eng:
                eng.module.handle_event = _original_handle_event
            _original_handle_event = None

        _monitoring = False
        _event_log.clear()
        print("[debug] Monitor reset")

    except Exception as e:
        print(f"[debug] ERROR resetting: {e}")


if __name__ == "__main__":
    print(__doc__)
