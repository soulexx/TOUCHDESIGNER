# Fix Video Control - Remove expression from index parameter
# Paste this into the TouchDesigner Textport:

video_top = op("/project1/media/moviefilein1")

if not video_top:
    print("[ERROR] Video TOP not found!")
else:
    print(f"[FIX] Found video TOP: {video_top.path}")

    # Check current state
    if hasattr(video_top.par, 'index'):
        old_expr = video_top.par.index.expr if video_top.par.index.mode else None
        old_mode = video_top.par.index.mode
        old_value = video_top.par.index.eval()

        print(f"  Current mode: {old_mode}")
        print(f"  Current expr: {old_expr}")
        print(f"  Current value: {old_value}")

        # Remove the expression and set to constant mode
        video_top.par.index.mode = ParMode.CONSTANT
        video_top.par.index.val = 0

        print("\n[FIXED]")
        print("  - Removed expression from 'index' parameter")
        print("  - Set mode to CONSTANT")
        print("  - Reset to frame 0")
        print("\n  Now the fader can control the video position!")

        # Set up the video path in project storage
        project = op("/project1")
        project.store("VIDEO_TOP_PATH", "/project1/media/moviefilein1")
        print("  - Configured VIDEO_TOP_PATH")

        # Test it
        try:
            import sys
            if r"c:\_DEV\TOUCHDESIGNER\src" not in sys.path:
                sys.path.insert(0, r"c:\_DEV\TOUCHDESIGNER\src")
            import video_control
            vc = video_control.get_controller()
            info = vc.info()
            print(f"\n[TEST] Video info:")
            print(f"  Total frames: {info.total_frames}")
            print(f"  Current frame: {info.frame}")

            # Test scrubbing to middle
            vc.set_normalized_time(0.5)
            info2 = vc.info()
            print(f"\n[TEST] Set to 50%:")
            print(f"  Frame: {info2.frame}")

            # Reset to start
            vc.set_normalized_time(0.0)
            print("\n[SUCCESS] Video control is working!")
            print("Now switch to Menu 5 and move Fader 1 to scrub through the video.")

        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("[ERROR] Video TOP has no 'index' parameter!")
