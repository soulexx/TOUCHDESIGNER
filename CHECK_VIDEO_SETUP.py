# Diagnose script - paste into Textport
import sys
sys.path.insert(0, r"c:\_DEV\TOUCHDESIGNER\src")

video_top = op("/project1/media/moviefilein1")
if not video_top:
    print("[ERROR] Video TOP not found at /project1/media/moviefilein1")
else:
    print(f"[OK] Video TOP found: {video_top.path}")
    print(f"  Type: {video_top.type}")

    # Check play mode
    if hasattr(video_top.par, 'playmode'):
        print(f"  Play Mode: {video_top.par.playmode}")

    # Check if using index or timecode
    if hasattr(video_top.par, 'index'):
        print(f"  Index parameter: {video_top.par.index.val} (mode: {video_top.par.index.mode})")
        print(f"  Index expression: {video_top.par.index.expr if video_top.par.index.mode else 'None'}")

    # Check total frames
    if hasattr(video_top, 'numFrames'):
        print(f"  Total frames: {video_top.numFrames}")
    elif hasattr(video_top, 'numImages'):
        print(f"  Total images: {video_top.numImages}")

    # Check rate
    if hasattr(video_top.par, 'rate'):
        print(f"  Frame rate: {video_top.par.rate}")

    # Check current playback state
    if hasattr(video_top.par, 'play'):
        playing = video_top.par.play.eval()
        print(f"  Playing: {bool(playing)}")

    # Check for any CHOPs connected to index
    if hasattr(video_top.par, 'index'):
        connections = video_top.par.index.inputs
        if connections:
            print(f"  Index has {len(connections)} input(s):")
            for conn in connections:
                print(f"    - {conn}")
        else:
            print("  Index has no CHOP inputs")

    print("\n[Recommendation]")
    print("For smooth scrubbing, the 'index' parameter should:")
    print("  1. NOT have an expression")
    print("  2. Be set directly from Python")
    print("  3. OR use a Lag CHOP for smoothing")
