"""Test palette sync with debug output."""
import time

base = op('/project1')
base.store('PALETTE_SYNC_ENABLED', True)
print("✅ PALETTE_SYNC_ENABLED = True\n")

# Load modules
pump = mod('/project1/palette_logic/pump')
state = mod('/project1/palette_logic/state')

# Reset
st = state.state
st.last_activity = 0.0
st.last_subscribe = 0.0
st.last_count_request = 0.0

# Inject a small count to test
print("Injecting test count: ip=3")
pump.queue_counts(base, {'ip': 3})

print("\nWaiting 5 seconds for responses...\n")
time.sleep(5)

# Check results
print("\n" + "=" * 70)
print("RESULTS:")
print("=" * 70)
print(f"IP Count: {st.counts.get('ip', 0)}")
print(f"IP Queue: {list(st.queues.get('ip', []))}")
print(f"IP Active: {st.active.get('ip')}")

# Check table
table = base.op("palette_logic/pal_ip")
if table and table.numRows > 1:
    print(f"\nTable rows: {table.numRows}")
    for row in range(1, min(4, table.numRows)):
        data = [table[row, col].val for col in range(min(4, table.numCols))]
        print(f"  Row {row}: {data}")
else:
    print("\n❌ Table empty or not found")
