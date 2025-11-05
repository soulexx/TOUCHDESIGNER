# Check video TOP play settings
video_top = op("/project1/media/moviefilein1")

if not video_top:
    print("[ERROR] Video TOP not found")
else:
    print(f"[CHECK] Video TOP: {video_top.path}")

    # Check Play state
    if hasattr(video_top.par, 'play'):
        play_val = video_top.par.play.eval()
        print(f"  Play: {play_val} ({'ON - VIDEO IS PLAYING!' if play_val else 'OFF - good'})")
        if play_val:
            print("  [FIX] Setting Play to OFF...")
            video_top.par.play.val = 0
            print("  [DONE] Play is now OFF")

    # Check Play Mode
    if hasattr(video_top.par, 'playmode'):
        mode = video_top.par.playmode.eval()
        print(f"  Play Mode: {mode}")
        if mode != 'indexmode':
            print("  [FIX] Setting Play Mode to 'indexmode'...")
            video_top.par.playmode = 'indexmode'
            print("  [DONE] Play Mode is now 'indexmode'")

    # Check Index
    if hasattr(video_top.par, 'index'):
        idx = video_top.par.index.eval()
        mode = video_top.par.index.mode
        expr = video_top.par.index.expr if mode else None
        print(f"  Index: {idx} (mode={mode})")
        if expr:
            print(f"  Index Expression: {expr}")
            print("  [WARNING] Index has an expression! This will override Python values!")

    print("\n[SOLUTION]")
    print("For scrubbing to work:")
    print("  1. Play must be OFF (or video will auto-play)")
    print("  2. Play Mode should be 'indexmode' or 'Specify Index'")
    print("  3. Index parameter should have NO expression")
