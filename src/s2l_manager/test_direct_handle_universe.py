"""Test handle_universe directly with full debug output."""

import sys
import importlib

# Setup paths
sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)

# FORCE reload with DEBUG enabled
import sacn_dispatch
importlib.reload(sacn_dispatch)

# Enable debug mode
sacn_dispatch.DEBUG_RAW = True

print("=" * 60)
print("DIRECT TEST: sacn_dispatch.handle_universe()")
print("=" * 60)

# Get DMX data
uni16 = op('/project1/io/EOS_Universe_016')
if not uni16:
    print("❌ ERROR: DMX CHOP not found")
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

    print(f"✅ Payload created: {len(payload)} bytes")
    print(f"   First 20: {list(payload[:20])}")
    print()

    # Clear cache to force fresh load
    sacn_dispatch._instances_cache.clear()
    print("✅ Cleared instances cache")
    print()

    print("=" * 60)
    print("Calling handle_universe(payload, 16)...")
    print("=" * 60)

    # This should print debug info AND update the tables
    sacn_dispatch.handle_universe(payload, 16)

    print()
    print("=" * 60)
    print("Check results:")
    print("=" * 60)

    # Check values table
    values = op('/project1/src/s2l_manager/values')
    if values:
        print(f"values table: {values.numRows} rows")
        for r in range(1, min(10, values.numRows)):
            inst = values[r, 0].val
            param = values[r, 1].val
            val = values[r, 2].val
            if inst == 'S2L_UNIT_1':
                print(f"  {inst}:{param} = {val}")
    else:
        print("❌ values table not found")

print("=" * 60)
