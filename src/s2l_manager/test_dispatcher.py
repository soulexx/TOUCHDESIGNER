"""Test script to clear values table and check if dispatcher is working."""

# Clear the values table
values = op('/project1/src/s2l_manager/values')
values.clear()
values.appendRow(['instance', 'parameter', 'value'])

print("=" * 60)
print("VALUES TABLE CLEARED")
print("=" * 60)
print(f"Rows: {values.numRows}, Cols: {values.numCols}")
print()

# Check if DMX is coming in
uni16 = op('/project1/io/EOS_Universe_016')
if uni16:
    print("DMX INPUT CHECK:")
    print(f"  Channel 11 (Sensitivity): {uni16[10].eval()}")
    print(f"  Channel 12 (Threshold):   {uni16[11].eval()}")
    print(f"  Channel 13 (LowCut_Hz):   {uni16[12].eval()}")
    print()
else:
    print("ERROR: Cannot find /project1/io/EOS_Universe_016")
    print()

# Check if frame_tick is running
frame_tick = op('/project1/io/frame_tick')
if frame_tick:
    print(f"frame_tick found: {frame_tick}")
else:
    print("ERROR: Cannot find /project1/io/frame_tick")

# Check if sacn_dispatch module loads
try:
    import sys
    sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
    if sacn_path not in sys.path:
        sys.path.insert(0, sacn_path)

    import sacn_dispatch
    print(f"sacn_dispatch module loaded: {sacn_dispatch}")
    print(f"  has handle_universe: {hasattr(sacn_dispatch, 'handle_universe')}")
except Exception as e:
    print(f"ERROR loading sacn_dispatch: {e}")

print()
print("=" * 60)
print("Now change values in Eos and watch the textport.")
print("You should see: [s2l_manager] S2L_UNIT_1:Sensitivity -> <value>")
print("=" * 60)
