"""Manually trigger the dispatcher to see if it works."""

import sys
sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)

import sacn_dispatch

# Get the DMX CHOP
chop = op('/project1/io/EOS_Universe_016')
if not chop:
    print("ERROR: Cannot find DMX CHOP")
else:
    print(f"Found CHOP: {chop}")
    print(f"  Channels: {chop.numChans}")
    print(f"  Samples: {chop.numSamples}")

    # Check Universe parameter
    universe_par = getattr(chop.par, "Universe", None)
    if universe_par:
        universe = int(universe_par.eval())
        print(f"  Universe parameter: {universe}")
    else:
        print("  No Universe parameter found - using default 16")
        universe = 16

    # Convert CHOP to bytes (same as frame_tick does)
    if chop.numSamples == 0:
        print("  ERROR: No samples in CHOP")
    else:
        data = []
        for channel in chop.chans():
            raw = channel[0]
            value = max(0.0, min(255.0, raw))
            data.append(int(round(value)))

        # Show first 20 bytes
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
        print("CALLING sacn_dispatch.handle_universe()...")
        print("=" * 60)

        # This should trigger the dispatcher and write to values table
        sacn_dispatch.handle_universe(payload, universe)

        print()
        print("=" * 60)
        print("Check values table now:")
        values = op('/project1/src/s2l_manager/values')
        print(f"  Rows: {values.numRows}")
        for i in range(min(10, values.numRows)):
            print(f"  Row {i}: {values[i, 0].val} | {values[i, 1].val} | {values[i, 2].val}")
        print("=" * 60)
