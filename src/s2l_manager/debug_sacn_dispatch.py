"""Debug why sacn_dispatch doesn't find instances."""

import sys

# Add paths
sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)

s2l_path = 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit'
if s2l_path not in sys.path:
    sys.path.insert(0, s2l_path)

print("=" * 60)
print("DEBUG: sacn_dispatch instance loading")
print("=" * 60)

# Import s2l_unit
try:
    import s2l_unit as s2l
    print(f"✅ s2l_unit module loaded: {s2l}")
except Exception as e:
    print(f"❌ ERROR loading s2l_unit: {e}")
    import traceback
    traceback.print_exc()

print()

# Try to load instances
try:
    print("Loading instances...")
    all_instances = s2l.load_instances()
    print(f"✅ Total instances loaded: {len(all_instances)}")

    for inst in all_instances:
        print(f"  - {inst.instance}: universe={inst.universe}, enabled={inst.enabled}, start={inst.start_address}")

except Exception as e:
    print(f"❌ ERROR loading instances: {e}")
    import traceback
    traceback.print_exc()

print()

# Check instances for universe 16
try:
    print("Filtering for Universe 16...")
    uni16_instances = [inst for inst in all_instances if inst.enabled and inst.universe == 16]
    print(f"✅ Universe 16 instances: {len(uni16_instances)}")

    for inst in uni16_instances:
        print(f"  - {inst.instance}: start={inst.start_address}")

except Exception as e:
    print(f"❌ ERROR filtering instances: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

# Now try to decode some DMX
uni16_chop = op('/project1/io/EOS_Universe_016')
if uni16_chop and len(uni16_instances) > 0:
    print("Testing DMX decode...")

    # Convert CHOP to bytes
    data = []
    for channel in uni16_chop.chans():
        raw = channel[0]
        value = max(0.0, min(255.0, raw))
        data.append(int(round(value)))

    # Pad to 512
    if len(data) > 512:
        data = data[-512:]
    elif len(data) < 512:
        data.extend([0] * (512 - len(data)))

    payload = bytes(data)

    print(f"  Payload size: {len(payload)} bytes")
    print(f"  First 20 bytes: {list(payload[:20])}")
    print()

    try:
        print("  Calling s2l.decode_universe()...")
        values = s2l.decode_universe(payload, uni16_instances, scaling=False)
        print(f"  ✅ Decoded {len(values)} instance(s)")

        for inst_name, params in values.items():
            print(f"    {inst_name}:")
            for key, val in params.items():
                if val != 0:  # Only show non-zero
                    print(f"      {key}: {val}")

    except Exception as e:
        print(f"  ❌ ERROR decoding: {e}")
        import traceback
        traceback.print_exc()

print("=" * 60)
