# Quick setup for video control
# Copy/paste this into the TouchDesigner Textport:

project = op("/project1")
project.store("VIDEO_TOP_PATH", "/project1/media/moviefilein1")
print("[video] Path configured: /project1/media/moviefilein1")

# Test it
try:
    import sys
    sys.path.insert(0, r"c:\_DEV\TOUCHDESIGNER\src")
    import video_control
    vc = video_control.get_controller()
    info = vc.info()
    print(f"[video] Total frames: {info.total_frames}")
    print(f"[video] Current frame: {info.frame}")
except Exception as e:
    print(f"[video] Error: {e}")
