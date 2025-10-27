"""Simulate EOS count response to test if handler works."""

# Get handler module
base = op('/project1')
handler_mod = mod('/project1/palette_logic/eos_notify_handler')

print("\n=== SIMULATING EOS COUNT RESPONSE ===\n")

# Simulate: /eos/out/get/ip/count with value 42
address = "/eos/out/get/ip/count"
args = [42.0]

print(f"Simulating OSC: {address} {args}")

try:
    handler_mod.on_osc_receive(address, args, absTime.seconds)
    print("✅ Handler called successfully")
except Exception as e:
    print(f"❌ Handler error: {e}")
    import traceback
    traceback.print_exc()

# Check state
import time
time.sleep(0.1)

state_mod = mod('/project1/palette_logic/state')
st = state_mod.state

print(f"\nAfter simulation:")
print(f"  Counts: {dict(st.counts)}")
print(f"  ip queue: {list(st.queues['ip'])[:5]}... ({len(st.queues['ip'])} total)")
print(f"  ip active: {st.active['ip']}")

# Check table
table = base.op("palette_logic/pal_ip")
print(f"  pal_ip table: {table.numRows} rows")

print("\n=== END SIMULATION ===\n")
