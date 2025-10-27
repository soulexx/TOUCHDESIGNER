"""Debug script to check palette sync status in TouchDesigner Textport."""
import time

# Get modules
base = op('/project1')
state_mod = mod('/project1/palette_logic/state')
pump_mod = mod('/project1/palette_logic/pump')

st = state_mod.state

print("\n=== PALETTE SYNC DEBUG ===\n")

# Check if sync is enabled
enabled = bool(base.fetch("PALETTE_SYNC_ENABLED", False))
print(f"PALETTE_SYNC_ENABLED: {enabled}")

# Check OSC Out
osc = base.op("io/oscout1")
if osc:
    print(f"OSC Out: {osc.par.address} port {osc.par.port}")
else:
    print("❌ OSC Out not found!")

# Check counts
print(f"\nCounts: {dict(st.counts)}")

# Check queues
print("\nQueues:")
for ptype in state_mod.ORDER:
    queue = list(st.queues[ptype])
    active = st.active[ptype]
    print(f"  {ptype}: active={active}, queue={queue[:10]}{'...' if len(queue) > 10 else ''} ({len(queue)} total)")

# Check tables
print("\nTables:")
for ptype in state_mod.ORDER:
    table = base.op(f"palette_logic/pal_{ptype}")
    if table:
        print(f"  pal_{ptype}: {table.numRows} rows x {table.numCols} cols")
        if table.numRows > 1:
            # Show first data row (row 1, after header)
            row_data = [table[1, col].val for col in range(min(4, table.numCols))]
            print(f"    Row 1: {row_data}")
    else:
        print(f"  pal_{ptype}: ❌ NOT FOUND")

# Check last activity
now = time.perf_counter()
print(f"\nLast activity: {now - st.last_activity:.1f}s ago")
print(f"Last subscribe: {now - st.last_subscribe:.1f}s ago")
print(f"Last count request: {now - st.last_count_request:.1f}s ago")

# Show sent timestamps
print("\nLast request sent:")
for ptype in state_mod.ORDER:
    if st.sent_at[ptype] > 0:
        print(f"  {ptype}: {now - st.sent_at[ptype]:.1f}s ago (attempts: {st.attempts[ptype]})")

print("\n=== END DEBUG ===\n")
