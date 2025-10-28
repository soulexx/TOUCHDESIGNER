"""Test if frame_tick is actually being called every frame."""

print("=" * 60)
print("IS FRAME_TICK RUNNING?")
print("=" * 60)
print()

# Get frame_tick
frame_tick = op('/project1/io/frame_tick')

if not frame_tick:
    print("❌ frame_tick not found")
else:
    print(f"✅ frame_tick found: {frame_tick}")
    print()

    # Add a debug counter to see if it runs
    print("Adding debug counter to frame_tick...")
    print()

    # Read current code
    current_code = frame_tick.text

    # Check if it already has a counter
    if '_debug_counter' in current_code:
        print("⚠️  Debug counter already exists")
    else:
        # Add counter at the top
        new_code = """# DEBUG: Counter to test if this runs
_debug_counter = 0

""" + current_code

        # Replace onFrameStart to increment counter
        new_code = new_code.replace(
            'def onFrameStart(dat):',
            '''def onFrameStart(dat):
    global _debug_counter
    _debug_counter += 1
    if _debug_counter % 60 == 0:  # Print every 60 frames (1 second at 60fps)
        print(f"[frame_tick] Running... counter={_debug_counter}")
'''
        )

        frame_tick.text = new_code
        print("✅ Added debug counter")

    print()
    print("=" * 60)
    print("NOW WATCH THE TEXTPORT")
    print("=" * 60)
    print()
    print("If frame_tick is running, you should see every second:")
    print("  [frame_tick] Running... counter=60")
    print("  [frame_tick] Running... counter=120")
    print("  ... etc")
    print()
    print("If you DON'T see these messages, frame_tick is NOT running!")
    print()
    print("Wait 5 seconds and check...")
    print("=" * 60)
