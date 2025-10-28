"""Check if frame_tick is actually calling our dispatcher."""

print("=" * 60)
print("FRAME_TICK STATUS CHECK")
print("=" * 60)

# Check frame_tick DAT
frame_tick = op('/project1/io/frame_tick')
if frame_tick:
    print(f"✅ frame_tick: {frame_tick}")
    print(f"   Frame Start enabled: {frame_tick.par.framestart.eval()}")
    print()

    # Show the code in frame_tick
    print("Frame tick code (first 30 lines):")
    print("-" * 60)
    lines = frame_tick.text.split('\n')[:30]
    for i, line in enumerate(lines, 1):
        print(f"{i:3}: {line}")
    print("-" * 60)
else:
    print("❌ frame_tick not found")

print()

# Check DMX input
uni16 = op('/project1/io/EOS_Universe_016')
if uni16:
    print(f"✅ DMX Input: {uni16}")
    print(f"   Ch11 (Sensitivity): {uni16[10].eval()}")
    print(f"   Ch12 (Threshold):   {uni16[11].eval()}")
else:
    print("❌ DMX input not found")

print()

# Check values table
values = op('/project1/src/s2l_manager/values')
if values:
    print(f"values table: {values.numRows} rows, {values.numCols} cols")

    if values.numRows > 1:
        print("First few S2L_UNIT_1 entries:")
        for r in range(1, min(15, values.numRows)):
            inst = values[r, 0].val
            param = values[r, 1].val
            val = values[r, 2].val
            if inst == 'S2L_UNIT_1':
                print(f"  {inst} | {param} | {val}")
    else:
        print("  Table is empty (only header)")
else:
    print("❌ values table not found")

print()

# Check if subs are moving - check audio_eos_exec
audio_exec = op('/project1/src/s2l_manager/audio_eos_exec')
if audio_exec:
    print(f"✅ audio_eos_exec: {audio_exec}")

    # Check if it has Frame Start enabled
    if hasattr(audio_exec.par, 'framestart'):
        is_enabled = audio_exec.par.framestart.eval()
        print(f"   Frame Start enabled: {is_enabled}")

        if is_enabled:
            print("   ⚠️  audio_eos_exec is running on Frame Start!")
            print("   This means OSC is being sent every frame")
            print("   BUT it might not be using DMX parameters!")
    else:
        print("   No framestart parameter")
else:
    print("❌ audio_eos_exec not found")

print()
print("=" * 60)
print("DIAGNOSIS:")
print("=" * 60)

if values and values.numRows == 1:
    print("❌ values table is empty")
    print("   → frame_tick is NOT calling sacn_dispatch properly")
    print("   → OR sacn_dispatch is not writing to values table")
    print()
    print("SOLUTION:")
    print("1. Check that /project1/io/frame_tick code imports sacn_dispatch")
    print("2. Make sure it calls sacn_dispatch.handle_universe()")
    print("3. The dispatcher module needs to be loaded in TouchDesigner")

if audio_exec and hasattr(audio_exec.par, 'framestart') and audio_exec.par.framestart.eval():
    print()
    print("✅ audio_eos_exec IS running!")
    print("   This explains why subs are moving")
    print()
    print("   BUT: If values table is empty, audio_eos_exec is using")
    print("   DEFAULT parameters, not DMX parameters from Eos!")

print("=" * 60)
