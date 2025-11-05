# Build Complete Video Transport System
# Run this in Textport to set up the CHOP network

media = op('/project1/media')
movie = op('/project1/media/moviefilein1')

if not movie:
    print("[ERROR] moviefilein1 not found!")
else:
    total_frames = movie.numImages if hasattr(movie, 'numImages') else 126415
    print(f"[INFO] Video has {total_frames} frames")

    # 1. Create Constant CHOP for fader input (Bridge from Python)
    print("\n[1] Creating fader_input CHOP...")
    fader_input = op('/project1/media/fader_input')
    if not fader_input:
        fader_input = media.create(constantCHOP, 'fader_input')
    fader_input.par.name0 = 'normalized'
    fader_input.par.value0 = 0
    print(f"  Created: {fader_input.path}")

    # 2. Create play/stop control CHOP
    print("\n[2] Creating transport_control CHOP...")
    transport = op('/project1/media/transport_control')
    if not transport:
        transport = media.create(constantCHOP, 'transport_control')
    transport.par.name0 = 'playing'
    transport.par.value0 = 0
    transport.par.name1 = 'scrubbing'
    transport.par.value1 = 0
    print(f"  Created: {transport.path}")

    # 3. Math CHOP: Scale fader (0-1) to frames
    print("\n[3] Setting up math1 (scale to frames)...")
    math1 = op('/project1/media/math1')
    if math1:
        # Connect fader_input
        math1.par.chopop = fader_input.path
        math1.par.fromrange1 = 0
        math1.par.fromrange2 = 1
        math1.par.torange1 = 0
        math1.par.torange2 = total_frames - 1
        print(f"  Connected: {fader_input.path} -> math1")
        print(f"  Range: 0-1 -> 0-{total_frames-1}")
    else:
        print("  [WARNING] math1 not found, create it manually")

    # 4. Speed CHOP for auto-play
    print("\n[4] Setting up speed...")
    # Use limit1 as the speed source
    limit1 = op('/project1/media/limit1')
    if limit1:
        limit1.par.limitmin = True
        limit1.par.limitmax = True
        limit1.par.min = 0
        limit1.par.max = total_frames - 1
        print(f"  Configured limit1: 0 to {total_frames-1}")

    # 5. Switch CHOP: Auto-play vs Manual scrub
    print("\n[5] Setting up switch1...")
    switch1 = op('/project1/media/switch1')
    if switch1:
        # Input 0: speed (from limit1)
        # Input 1: scrub (from math1)
        # Index: transport_control/scrubbing
        switch1.par.index = f"op('{transport.path}')['scrubbing']"
        print(f"  Switch index: scrubbing channel")
        print(f"  Input 0 (speed): Connect limit1 manually")
        print(f"  Input 1 (scrub): Connect math1 manually")
    else:
        print("  [WARNING] switch1 not found")

    # 6. Filter for smooth transitions
    print("\n[6] Filter is already set up")
    filter1 = op('/project1/media/filter1')
    if filter1:
        print(f"  filter1.par.filterwidth = {filter1.par.filterwidth.eval()}")

    # 7. Connect to moviefilein1
    print("\n[7] Setting up moviefilein1...")
    movie.par.playmode = 'indexmode'
    movie.par.play = 0
    # Index should already have: op('filter1')[0]
    print(f"  Play Mode: indexmode")
    print(f"  Index expression: {movie.par.index.expr if movie.par.index.mode else 'NONE - SET IT!'}")

    print("\n" + "="*60)
    print("MANUAL STEPS NEEDED:")
    print("="*60)
    print("\n1. Wire CHOPs in Network Editor:")
    print("   constant1 -> limit1 -> switch1 (input 0)")
    print("   fader_input -> math1 -> switch1 (input 1)")
    print("   switch1 -> filter1")
    print("\n2. Set moviefilein1 index parameter:")
    print("   Right-click index -> CHOP Reference -> filter1, channel 0")
    print("\n3. Test from Textport:")
    print("   # Move fader")
    print("   op('/project1/media/fader_input')['normalized'].val = 0.5")
    print("   op('/project1/media/transport_control')['scrubbing'].val = 1")
    print("\n4. Integrate with menu_engine.py (I'll provide code)")
    print("="*60)
