"""Update the frame_tick DAT with the new code."""

print("=" * 60)
print("UPDATE FRAME TICK")
print("=" * 60)
print()

# Read the new frame_tick code
with open('C:/_DEV/TOUCHDESIGNER/io/frame_tick_NEW.py', 'r') as f:
    new_code = f.read()

# Get the frame_tick DAT
frame_tick = op('/project1/io/frame_tick')

if not frame_tick:
    print("❌ frame_tick not found at /project1/io/frame_tick")
else:
    print(f"✅ Found frame_tick: {frame_tick}")
    print()

    # Update the text
    frame_tick.text = new_code
    print("✅ Updated frame_tick code")
    print()

    # Check if Frame Start is enabled
    if hasattr(frame_tick.par, 'framestart'):
        is_enabled = frame_tick.par.framestart.eval()
        print(f"   Frame Start: {is_enabled}")

        if not is_enabled:
            print("   ⚠️  Enabling Frame Start...")
            frame_tick.par.framestart = True
    print()

    print("=" * 60)
    print("TESTING...")
    print("=" * 60)

    # Test it once manually
    print("Executing frame_tick once manually...")
    exec(frame_tick.text)

    if 'onFrameStart' in dir():
        onFrameStart(frame_tick)
        print("✅ Executed successfully")
    else:
        print("❌ onFrameStart not found")

    print()

    # Check values table
    values = op('/project1/src/s2l_manager/values')
    if values:
        print(f"values table: {values.numRows} rows")

        if values.numRows > 1:
            print("✅ Data:")
            for r in range(1, min(8, values.numRows)):
                inst = values[r, 0].val
                param = values[r, 1].val
                val = values[r, 2].val
                if inst == 'S2L_UNIT_1' and param in ['Sensitivity', 'Threshold']:
                    print(f"  {inst} | {param} | {val}")

    print()
    print("=" * 60)
    print("NOW TEST AUTOMATIC UPDATES:")
    print("=" * 60)
    print("1. Open Textport (Alt+T)")
    print("2. Change DMX Channel 11 in Eos")
    print("3. You should see: [s2l_manager] S2L_UNIT_1:Sensitivity -> <value>")
    print()
    print("If you see that, automatic updates are working! 🎉")
    print("=" * 60)
