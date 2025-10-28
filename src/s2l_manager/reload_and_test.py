"""Reload sacn_dispatch module and test dispatcher."""

import sys
import importlib

# Ensure path is correct
sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)

# FORCE RELOAD the module to pick up our changes
if 'sacn_dispatch' in sys.modules:
    print("Reloading sacn_dispatch module...")
    import sacn_dispatch
    importlib.reload(sacn_dispatch)
else:
    print("Loading sacn_dispatch module for first time...")
    import sacn_dispatch

print(f"Module loaded: {sacn_dispatch}")
print(f"Module has 'op': {hasattr(sacn_dispatch, 'op')}")
if hasattr(sacn_dispatch, 'op'):
    print(f"  sacn_dispatch.op = {sacn_dispatch.op}")
print()

# Also reload dispatcher module
manager_path = 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager'
if manager_path not in sys.path:
    sys.path.insert(0, manager_path)

if 'dispatcher' in sys.modules:
    print("Reloading dispatcher module...")
    import dispatcher
    importlib.reload(dispatcher)
else:
    print("Loading dispatcher module for first time...")
    import dispatcher

print(f"Module loaded: {dispatcher}")
print(f"Module has 'op': {hasattr(dispatcher, 'op')}")
if hasattr(dispatcher, 'op'):
    print(f"  dispatcher.op = {dispatcher.op}")
print()

# Now test the dispatcher
chop = op('/project1/io/EOS_Universe_016')
if not chop:
    print("ERROR: Cannot find DMX CHOP")
else:
    print(f"Found CHOP: {chop}")

    # Convert CHOP to bytes
    if chop.numSamples == 0:
        print("  ERROR: No samples in CHOP")
    else:
        data = []
        for channel in chop.chans():
            raw = channel[0]
            value = max(0.0, min(255.0, raw))
            data.append(int(round(value)))

        print(f"  First 20 DMX values: {data[:20]}")

        # Pad to 512
        if len(data) > 512:
            data = data[-512:]
        elif len(data) < 512:
            data.extend([0] * (512 - len(data)))

        payload = bytes(data)
        print(f"  Payload size: {len(payload)} bytes")
        print()
        print("=" * 60)
        print("CALLING sacn_dispatch.handle_universe(payload, 16)...")
        print("=" * 60)

        # This should trigger the dispatcher and write to values table
        sacn_dispatch.handle_universe(payload, 16)

        print()
        print("=" * 60)
        print("Check values table now:")
        values = op('/project1/src/s2l_manager/values')
        print(f"  Rows: {values.numRows}")
        for i in range(min(10, values.numRows)):
            print(f"  Row {i}: {values[i, 0].val} | {values[i, 1].val} | {values[i, 2].val}")
        print("=" * 60)
