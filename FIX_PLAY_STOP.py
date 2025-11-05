# Fix Play/Stop functionality by replacing Speed CHOP with Count CHOP

media = op('/project1/media')
movie = op('/project1/media/moviefilein1')

if not movie:
    print("[ERROR] moviefilein1 not found!")
else:
    total_frames = movie.numImages if hasattr(movie, 'numImages') else 126415
    print(f"[INFO] Video has {total_frames} frames")

    # Delete old speed_auto if it exists
    speed_auto = op('/project1/media/speed_auto')
    if speed_auto:
        print(f"\n[1] Removing non-functional speed_auto...")
        speed_auto.destroy()

    # Create Count CHOP for auto-play
    print(f"\n[2] Creating count_auto CHOP...")
    count_auto = op('/project1/media/count_auto')
    if not count_auto:
        count_auto = media.create(countCHOP, 'count_auto')

    # Configure Count CHOP
    count_auto.par.limitmax = True
    count_auto.par.max = total_frames - 1
    count_auto.par.looproll = True  # Loop back to 0 when reaching max
    count_auto.par.threshold = total_frames - 1
    count_auto.par.count = 0  # Start at 0

    print(f"  Created: {count_auto.path}")
    print(f"  Range: 0 to {total_frames - 1}")
    print(f"  Parameters:")
    print(f"    - limitmax: {count_auto.par.limitmax.eval()}")
    print(f"    - max: {count_auto.par.max.eval()}")
    print(f"    - looproll: {count_auto.par.looproll.eval()}")

    # Connect count_auto -> limit1 -> switch2 (input 0)
    print(f"\n[3] Connecting count_auto to limit1...")
    limit1 = op('/project1/media/limit1')
    if limit1:
        limit1.setInput(0, count_auto)
        print(f"  Connected: count_auto -> limit1")
    else:
        print("  [ERROR] limit1 not found!")

    # Update transport_control
    transport = op('/project1/media/transport_control')
    if transport:
        print(f"\n[4] Resetting transport_control...")
        transport.par.value0 = 0  # playing = 0
        transport.par.value1 = 1  # scrubbing = 1 (default to scrub mode)
        print(f"  playing: {transport.par.value0.eval()}")
        print(f"  scrubbing: {transport.par.value1.eval()}")

    print("\n" + "="*60)
    print("PLAY/STOP CONTROLS:")
    print("="*60)
    print("\nTo PLAY:")
    print("  transport = op('/project1/media/transport_control')")
    print("  count_auto = op('/project1/media/count_auto')")
    print("  transport.par.value0 = 1  # playing on")
    print("  transport.par.value1 = 0  # scrubbing off")

    print("\nTo STOP:")
    print("  transport.par.value0 = 0  # playing off")
    print("  transport.par.value1 = 1  # scrubbing on")
    print("  count_auto.par.count = 0  # reset to start")

    print("\nTo PAUSE:")
    print("  transport.par.value0 = 0  # just stop counting")
    print("  transport.par.value1 = 1  # allow scrubbing")

    print("\n" + "="*60)
    print("TEST IT:")
    print("="*60)
    print("\n# Start playing:")
    print("op('/project1/media/transport_control').par.value0 = 1")
    print("op('/project1/media/transport_control').par.value1 = 0")
    print("\n# Stop and reset:")
    print("op('/project1/media/transport_control').par.value0 = 0")
    print("op('/project1/media/transport_control').par.value1 = 1")
    print("op('/project1/media/count_auto').par.count = 0")
    print("="*60)
