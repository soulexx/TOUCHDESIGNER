"""Trace through handle_universe to see where it stops."""

import sys

sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)

# Force fresh import
if 'sacn_dispatch' in sys.modules:
    del sys.modules['sacn_dispatch']

import sacn_dispatch

print("=" * 60)
print("TRACE: handle_universe execution")
print("=" * 60)

# Get DMX data
uni16 = op('/project1/io/EOS_Universe_016')
if not uni16:
    print("❌ No DMX CHOP")
else:
    # Convert to bytes
    data = []
    for channel in uni16.chans():
        raw = channel[0]
        value = max(0.0, min(255.0, raw))
        data.append(int(round(value)))

    if len(data) > 512:
        data = data[-512:]
    elif len(data) < 512:
        data.extend([0] * (512 - len(data)))

    payload = bytes(data)

    print(f"✅ Payload: {len(payload)} bytes")
    print(f"   First 20: {list(payload[:20])}")
    print()

    # Clear cache
    sacn_dispatch._instances_cache.clear()
    print("✅ Cache cleared")
    print()

    # Step by step execution
    print("Step 1: Check if payload is empty...")
    if not payload:
        print("  ❌ Payload is empty - function returns early")
    else:
        print("  ✅ Payload has data")

    print()
    print("Step 2: Get instances for universe 16...")
    instances = sacn_dispatch._instances_for_universe(16)
    print(f"  Found {len(instances)} instances")

    if not instances:
        print("  ❌ No instances - function returns early")
    else:
        print("  ✅ Instances found")
        for inst in instances[:3]:
            print(f"    - {inst.instance}")

    print()
    print("Step 3: Decode universe...")
    try:
        import s2l_unit as s2l
        values = s2l.decode_universe(payload, instances, scaling=False)
        print(f"  ✅ Decoded {len(values)} instance(s)")

        # Show first instance
        for inst_name, params in list(values.items())[:1]:
            print(f"    {inst_name}:")
            for key, val in params.items():
                if val != 0:
                    print(f"      {key}: {val}")

    except Exception as e:
        print(f"  ❌ Decode failed: {e}")
        values = None

    print()
    print("Step 4: Get defaults...")
    try:
        defaults = sacn_dispatch._get_defaults()
        print(f"  ✅ Got defaults")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        defaults = None

    print()
    print("Step 5: Get manager DAT...")
    target = op(sacn_dispatch.MANAGER_DAT_PATH)
    if not target:
        print(f"  ❌ Manager not found at {sacn_dispatch.MANAGER_DAT_PATH}")
    else:
        print(f"  ✅ Manager found: {target}")

    print()
    print("Step 6: Get update_from_dmx function...")
    if target:
        update = getattr(target.module, "update_from_dmx", None)
        if not callable(update):
            print(f"  ❌ update_from_dmx not callable")
        else:
            print(f"  ✅ update_from_dmx found: {update}")

            print()
            print("Step 7: Call update_from_dmx...")
            try:
                update(16, values, defaults)
                print(f"  ✅ Called successfully")
            except Exception as e:
                print(f"  ❌ Call failed: {e}")
                import traceback
                traceback.print_exc()

    print()
    print("Step 8: Check values table...")
    values_table = op('/project1/src/s2l_manager/values')
    if values_table:
        print(f"  values table: {values_table.numRows} rows")
        if values_table.numRows > 1:
            print("  ✅ Has data:")
            for r in range(1, min(5, values_table.numRows)):
                inst = values_table[r, 0].val
                param = values_table[r, 1].val
                val = values_table[r, 2].val
                if inst == 'S2L_UNIT_1':
                    print(f"    {inst} | {param} | {val}")
        else:
            print("  ❌ Empty")

print()
print("=" * 60)
print("Now calling sacn_dispatch.handle_universe() directly...")
print("=" * 60)

sacn_dispatch._instances_cache.clear()
sacn_dispatch.handle_universe(payload, 16)

print()
print("Check values table again:")
values_table = op('/project1/src/s2l_manager/values')
if values_table:
    print(f"  Rows: {values_table.numRows}")
    for r in range(1, min(5, values_table.numRows)):
        if r < values_table.numRows:
            inst = values_table[r, 0].val
            param = values_table[r, 1].val
            val = values_table[r, 2].val
            if inst == 'S2L_UNIT_1':
                print(f"  {inst} | {param} | {val}")

print("=" * 60)
