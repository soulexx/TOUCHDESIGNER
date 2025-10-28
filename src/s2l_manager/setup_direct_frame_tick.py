"""Setup the DIRECT frame tick that bypasses module caching."""

print("=" * 60)
print("SETUP DIRECT FRAME TICK")
print("=" * 60)
print()

print("MANUAL STEPS REQUIRED:")
print()
print("1. In TouchDesigner, go to /project1/io/")
print()
print("2. Create a new Execute DAT (or find existing frame_tick_direct):")
print("   - Right-click in network → Add Operator → DAT → Text")
print("   - Rename it to 'frame_tick_direct'")
print()
print("3. Configure the DAT:")
print("   - In parameter panel → DAT:")
print("   - Check 'Sync to File'")
print("   - File path: C:/_DEV/TOUCHDESIGNER/io/frame_tick_DIRECT.py")
print()
print("4. Enable Execute:")
print("   - In parameter panel → DAT Execute:")
print("   - Check 'Frame Start'")
print("   - This will call onFrameStart() every frame")
print()
print("5. DISABLE the old frame_tick:")
print("   - Go to /project1/io/frame_tick")
print("   - Uncheck 'Frame Start'")
print("   - (We don't want both running at once)")
print()
print("6. Test it:")
print("   - Change a DMX value in Eos")
print("   - Watch the textport for: [s2l_manager] S2L_UNIT_1:Sensitivity -> <value>")
print()
print("=" * 60)
print()

# Try to find if it already exists
frame_tick_direct = op('/project1/io/frame_tick_direct')

if frame_tick_direct:
    print("✅ frame_tick_direct ALREADY EXISTS!")
    print(f"   Path: {frame_tick_direct}")
    print()

    # Check if it's synced to file
    if hasattr(frame_tick_direct.par, 'file'):
        file_param = frame_tick_direct.par.file.eval()
        print(f"   File sync: {file_param}")

        if 'frame_tick_DIRECT.py' in file_param:
            print("   ✅ Synced to correct file")
        else:
            print("   ⚠️  Not synced to frame_tick_DIRECT.py")
            print("   → Set file parameter to: C:/_DEV/TOUCHDESIGNER/io/frame_tick_DIRECT.py")

    # Check if Frame Start is enabled
    if hasattr(frame_tick_direct.par, 'framestart'):
        is_enabled = frame_tick_direct.par.framestart.eval()
        print(f"   Frame Start: {is_enabled}")

        if is_enabled:
            print("   ✅ Frame Start is enabled - good!")
        else:
            print("   ⚠️  Frame Start is DISABLED")
            print("   → Enable it in DAT Execute panel")

    print()
    print("You can test it now by changing DMX values in Eos!")

else:
    print("⚠️  frame_tick_direct DOES NOT EXIST YET")
    print()
    print("Please follow the manual steps above to create it.")

print()
print("=" * 60)
print()

# Test the current setup
print("CURRENT STATUS:")
print()

# Check old frame_tick
old_frame_tick = op('/project1/io/frame_tick')
if old_frame_tick and hasattr(old_frame_tick.par, 'framestart'):
    if old_frame_tick.par.framestart.eval():
        print("⚠️  OLD frame_tick is still enabled!")
        print("   You should disable it to avoid conflicts")

# Check dispatcher
dispatcher = op('/project1/src/s2l_manager/dispatcher')
if dispatcher:
    print("✅ Dispatcher found")

# Check DMX input
dmx = op('/project1/io/EOS_Universe_016')
if dmx:
    print(f"✅ DMX input found")
    print(f"   Ch11 (Sensitivity): {dmx[10].eval()}")
    print(f"   Ch12 (Threshold):   {dmx[11].eval()}")

# Check values table
values = op('/project1/src/s2l_manager/values')
if values:
    print(f"✅ values table: {values.numRows} rows")

print()
print("=" * 60)
