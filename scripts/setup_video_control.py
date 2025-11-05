"""Setup script for video control integration.

Run this from the TouchDesigner Textport or via scripts/live_command.py:

    import scripts.setup_video_control
    scripts.setup_video_control.setup()
"""

def setup():
    """Configure video control to point at /project1/media/moviefilein1."""
    try:
        project = op("/project1")
        video_path = "/project1/media/moviefilein1"

        # Store the path
        project.store("VIDEO_TOP_PATH", video_path)
        print(f"[video_control] VIDEO_TOP_PATH set to: {video_path}")

        # Verify the TOP exists
        video_top = op(video_path)
        if video_top:
            print(f"[video_control] Video TOP found: {video_top}")
            # Check if it has the expected parameters
            if hasattr(video_top.par, 'play'):
                print(f"[video_control] ✓ Video TOP has 'play' parameter")
            if hasattr(video_top.par, 'index'):
                print(f"[video_control] ✓ Video TOP has 'index' parameter")

            # Try to get video info
            try:
                import video_control
                vc = video_control.get_controller()
                info = vc.info()
                print(f"[video_control] Video info:")
                print(f"  - Path: {info.path}")
                print(f"  - Total frames: {info.total_frames}")
                print(f"  - Current frame: {info.frame}")
                print(f"  - Length: {info.length_seconds:.2f}s" if info.length_seconds else "  - Length: unknown")
                print(f"  - Frame rate: {info.rate} fps" if info.rate else "  - Frame rate: unknown")
            except Exception as e:
                print(f"[video_control] Warning: Could not get video info: {e}")
        else:
            print(f"[video_control] WARNING: Video TOP not found at {video_path}")
            print("[video_control] Please check the path and update if needed")

        return True
    except Exception as e:
        print(f"[video_control] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    setup()
