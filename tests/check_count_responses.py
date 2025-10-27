"""Check if EOS count responses are arriving at OSC In."""

print("\n=== CHECKING FOR EOS COUNT RESPONSES ===\n")

# Find OSC In operator
base = op('/project1')
oscin = None

# Try common paths
for path in ['/project1/io/oscin1', '/project1/oscin1', '/project1/io/oscin']:
    try:
        oscin = op(path)
        if oscin:
            print(f"Found OSC In: {path}")
            break
    except:
        pass

if not oscin:
    # Search for it
    oscin_list = base.findChildren(name="oscin*", maxDepth=3)
    if oscin_list:
        oscin = oscin_list[0]
        print(f"Found OSC In: {oscin.path}")

if not oscin:
    print("❌ OSC In not found!")
else:
    print(f"OSC In has {oscin.numRows} messages\n")

    # Look for EOS count responses
    count_messages = []
    for i in range(oscin.numRows):
        addr = oscin[i, 'address'].val if oscin.numCols > 0 else ""
        if '/eos/out/get/' in addr and '/count' in addr:
            count_messages.append((i, addr, oscin[i, 'value0'].val if oscin.numCols > 1 else ""))

    if count_messages:
        print(f"✅ Found {len(count_messages)} count response(s):")
        for row, addr, val in count_messages[-5:]:  # Show last 5
            print(f"  Row {row}: {addr} = {val}")
    else:
        print("❌ No count responses found in OSC In")
        print("\nLooking for ANY /eos/out messages:")
        eos_out = []
        for i in range(max(0, oscin.numRows-20), oscin.numRows):
            addr = oscin[i, 'address'].val if oscin.numCols > 0 else ""
            if '/eos/out/' in addr:
                eos_out.append((i, addr))
        if eos_out:
            print(f"Found {len(eos_out)} /eos/out messages (last 20 rows):")
            for row, addr in eos_out[-10:]:
                print(f"  Row {row}: {addr}")
        else:
            print("  No /eos/out messages at all!")

# Check if palette sync is enabled and subscribed
print("\n=== PALETTE SYNC STATUS ===")
enabled = bool(base.fetch("PALETTE_SYNC_ENABLED", False))
print(f"PALETTE_SYNC_ENABLED: {enabled}")

state_mod = mod('/project1/palette_logic/state')
st = state_mod.state
print(f"Subscribed: {st.subscribed}")

import time
now = time.perf_counter()
print(f"Last subscribe: {now - st.last_subscribe:.1f}s ago")
print(f"Last count request: {now - st.last_count_request:.1f}s ago")

print("\n=== END CHECK ===\n")
