# Force reload video_control module
# Paste this into the Textport:

import sys
import importlib

# Ensure src path is in sys.path
src_path = r"c:\_DEV\TOUCHDESIGNER\src"
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Remove cached module
if 'video_control' in sys.modules:
    print("[reload] Removing cached video_control module")
    del sys.modules['video_control']

if 'video_control.controller' in sys.modules:
    print("[reload] Removing cached video_control.controller module")
    del sys.modules['video_control.controller']

# Import fresh
import video_control
print(f"[reload] Imported video_control from: {video_control.__file__}")

# Reset the singleton
video_control._controller_singleton = None

# Test it
try:
    vc = video_control.get_controller()
    print("[reload] Testing video control...")

    # Set to 50%
    vc.set_normalized_time(0.5)

    # Check the result
    info = vc.info()
    print(f"[reload] Current frame: {info.frame}/{info.total_frames}")

    # Set to 0%
    vc.set_normalized_time(0.0)
    info2 = vc.info()
    print(f"[reload] Reset to frame: {info2.frame}")

    print("\n[SUCCESS] Video control module reloaded!")
    print("Now move Fader 1 on Menu 5 to test scrubbing.")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
