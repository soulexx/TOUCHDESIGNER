"""
Diagnose why DMX values are not changing in the values table.

This script checks the entire DMX processing pipeline step-by-step:
1. DMX CHOP input (raw network data)
2. frame_tick processing (conversion to bytes)
3. sacn_dispatch decoding
4. dispatcher table updates

Run this script in TouchDesigner's Textport to debug the issue.
"""

print("=" * 80)
print("DMX VALUE CHANGE DIAGNOSTIC")
print("=" * 80)
print()

# Step 1: Check DMX CHOP
print("STEP 1: Checking DMX CHOP Input")
print("-" * 80)
uni16 = op('/project1/io/EOS_Universe_016')
if not uni16:
    print("❌ ERROR: Cannot find /project1/io/EOS_Universe_016")
    print("   The DMX input CHOP is missing!")
else:
    print(f"✅ Found DMX CHOP: {uni16.path}")
    print(f"   Channels: {uni16.numChans}")
    print(f"   Samples: {uni16.numSamples}")

    # Check if it's active
    if hasattr(uni16.par, 'active'):
        is_active = uni16.par.active.eval()
        if is_active:
            print(f"   ✅ CHOP is active")
        else:
            print(f"   ❌ CHOP is NOT active (enable it!)")

    # Check universe
    if hasattr(uni16.par, 'universe'):
        universe = uni16.par.universe.eval()
        print(f"   Universe: {universe}")
        if universe != 16:
            print(f"   ⚠️  WARNING: Expected universe 16, got {universe}")

    # Show non-zero values
    print()
    print("   Non-zero DMX values (first 50 channels):")
    found_nonzero = False
    for i in range(min(50, uni16.numChans)):
        val = uni16[i].eval()
        if val != 0:
            print(f"     Channel {i+1} (DMX address {i+1}): {val}")
            found_nonzero = True

    if not found_nonzero:
        print("     ⚠️  No non-zero values found in first 50 channels!")
        print("     This means DMX data is either:")
        print("       - Not arriving from the network")
        print("       - All set to 0")
        print("       - Going to different DMX addresses")

print()
print()

# Step 2: Check frame_tick is running
print("STEP 2: Checking frame_tick.py execution")
print("-" * 80)
frame_tick_dat = op('/project1/io/frame_tick')
if not frame_tick_dat:
    print("❌ ERROR: Cannot find /project1/io/frame_tick")
else:
    print(f"✅ Found frame_tick DAT: {frame_tick_dat.path}")

    # Check if it has the debug counter
    if hasattr(frame_tick_dat.module, '_debug_counter'):
        counter = frame_tick_dat.module._debug_counter
        print(f"   Debug counter: {counter}")
        if counter > 0:
            print(f"   ✅ frame_tick is running (executed {counter} times)")
        else:
            print(f"   ⚠️  frame_tick has not executed yet!")
    else:
        print(f"   ⚠️  No debug counter found (old version?)")

print()
print()

# Step 3: Check sacn_exec trigger
print("STEP 3: Checking sacn_exec (CHOP Execute trigger)")
print("-" * 80)
sacn_exec = op('/project1/io/sacn_exec')
if not sacn_exec:
    print("❌ ERROR: Cannot find /project1/io/sacn_exec")
    print("   This is the CHOP Execute DAT that triggers frame_tick!")
else:
    print(f"✅ Found sacn_exec: {sacn_exec.path}")

    # Check if it has inputs
    if sacn_exec.inputs:
        print(f"   Inputs: {len(sacn_exec.inputs)}")
        for i, inp in enumerate(sacn_exec.inputs):
            print(f"     Input {i}: {inp}")
    else:
        print(f"   ⚠️  No inputs connected!")

print()
print()

# Step 4: Check instances configuration
print("STEP 4: Checking S2L instances configuration")
print("-" * 80)
try:
    import s2l_unit as s2l
    instances = s2l.load_instances()
    uni16_instances = [inst for inst in instances if inst.enabled and inst.universe == 16]

    print(f"   Total instances: {len(instances)}")
    print(f"   Enabled instances on universe 16: {len(uni16_instances)}")
    print()

    if uni16_instances:
        print("   Instance DMX address mapping:")
        for inst in uni16_instances:
            end_addr = inst.start_address + 18  # 19 slots total
            print(f"     {inst.instance}: DMX {inst.start_address}-{end_addr}")
    else:
        print("   ⚠️  No enabled instances found for universe 16!")

except Exception as e:
    print(f"   ❌ ERROR loading instances: {e}")

print()
print()

# Step 5: Check dispatcher and values table
print("STEP 5: Checking dispatcher and values table")
print("-" * 80)
dispatcher = op('/project1/src/s2l_manager/dispatcher')
if not dispatcher:
    print("❌ ERROR: Cannot find /project1/src/s2l_manager/dispatcher")
else:
    print(f"✅ Found dispatcher: {dispatcher.path}")

    # Check if it has the update function
    if hasattr(dispatcher.module, 'update_from_dmx'):
        print(f"   ✅ update_from_dmx function exists")

        # Check last values cache
        if hasattr(dispatcher.module, '_last_values'):
            last_vals = dispatcher.module._last_values
            print(f"   Last values cache: {len(last_vals)} instances")
            for inst_name, params in last_vals.items():
                print(f"     {inst_name}: {len(params)} parameters")
                # Show first few values
                for key, val in list(params.items())[:3]:
                    print(f"       {key}: {val}")
        else:
            print(f"   ⚠️  No _last_values cache found")
    else:
        print(f"   ❌ update_from_dmx function NOT found!")

print()

values_table = op('/project1/src/s2l_manager/values')
if not values_table:
    print("❌ ERROR: Cannot find /project1/src/s2l_manager/values table")
else:
    print(f"✅ Found values table: {values_table.path}")
    print(f"   Rows: {values_table.numRows}")
    print(f"   Columns: {values_table.numCols}")

    if values_table.numRows > 1:
        print()
        print("   Current table contents (first 10 rows):")
        for row in range(min(10, values_table.numRows)):
            if row == 0:
                print(f"     [Header] {values_table[row, 0].val} | {values_table[row, 1].val} | {values_table[row, 2].val}")
            else:
                print(f"     [{row}] {values_table[row, 0].val} | {values_table[row, 1].val} | {values_table[row, 2].val}")
    else:
        print("   ⚠️  Table is empty (only header row)!")

print()
print()

# Step 6: Manual test - read CHOP and decode
print("STEP 6: Manual DMX decode test")
print("-" * 80)
if uni16 and uni16.numChans > 0:
    try:
        import s2l_unit as s2l

        # Convert CHOP to bytes (same as frame_tick does)
        data = []
        for channel in uni16.chans():
            raw = channel[0]
            value = max(0.0, min(255.0, raw))
            data.append(int(round(value)))

        # Pad to 512
        if len(data) < 512:
            data.extend([0] * (512 - len(data)))
        elif len(data) > 512:
            data = data[:512]

        payload = bytes(data)

        print(f"   Converted CHOP to {len(payload)} byte payload")

        # Show first 20 bytes
        print(f"   First 20 bytes: {list(payload[:20])}")

        # Try to decode for universe 16
        instances = s2l.load_instances()
        uni16_instances = [inst for inst in instances if inst.enabled and inst.universe == 16]

        if uni16_instances:
            print()
            print("   Decoding instances (scaling=False):")
            decoded = s2l.decode_universe(payload, uni16_instances, scaling=False)

            for inst_name, params in decoded.items():
                print(f"     {inst_name}:")
                for key, val in params.items():
                    if val != 0:  # Only show non-zero
                        print(f"       {key}: {val}")
        else:
            print("   ⚠️  No instances to decode!")

    except Exception as e:
        print(f"   ❌ ERROR during manual decode: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   ⚠️  Cannot perform manual test (CHOP not found or empty)")

print()
print()

# Summary and recommendations
print("=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)
print()
print("Common issues and solutions:")
print()
print("1. DMX CHOP is inactive:")
print("   → Enable the CHOP parameter 'active'")
print()
print("2. DMX data not arriving:")
print("   → Check network connection (Eos → TouchDesigner)")
print("   → Check firewall settings (allow sACN multicast)")
print("   → Verify Eos is transmitting to correct universe")
print()
print("3. frame_tick not executing:")
print("   → Check sacn_exec CHOP Execute DAT is connected")
print("   → Verify the CHOP Execute is enabled")
print()
print("4. Wrong DMX addresses:")
print("   → Check instances.csv start_address values")
print("   → Ensure Eos fixture patch matches TouchDesigner config")
print()
print("5. Values decode but don't update table:")
print("   → Check dispatcher module is loaded correctly")
print("   → Enable DEBUG logging in sacn_dispatch.py (set DEBUG_RAW = True)")
print()
print("=" * 80)
