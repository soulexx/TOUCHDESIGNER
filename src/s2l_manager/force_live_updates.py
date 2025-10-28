"""
Force live DMX value updates without change detection.

This script modifies the dispatcher to update the values table every frame,
even if the DMX values haven't changed. Useful for debugging and monitoring.

Run this once to enable live updates, then check the values table.
"""

print("=" * 80)
print("FORCE LIVE DMX UPDATES")
print("=" * 80)
print()

# Get the dispatcher
dispatcher = op('/project1/src/s2l_manager/dispatcher')
if not dispatcher:
    print("❌ ERROR: Cannot find dispatcher at /project1/src/s2l_manager/dispatcher")
else:
    print(f"✅ Found dispatcher: {dispatcher.path}")

    # Clear the last values cache to force updates
    if hasattr(dispatcher.module, '_last_values'):
        dispatcher.module._last_values.clear()
        print("✅ Cleared _last_values cache")

    # Clear the table row cache
    if hasattr(dispatcher.module, '_table_row_cache'):
        dispatcher.module._table_row_cache.clear()
        print("✅ Cleared _table_row_cache")

    print()
    print("Now triggering a frame update...")

    # Manually trigger frame_tick
    frame_tick = op('/project1/io/frame_tick')
    if frame_tick:
        frame_tick.module.onFrameStart(frame_tick)
        print("✅ Triggered frame_tick")
    else:
        print("❌ Cannot find frame_tick")

    print()
    print("=" * 80)
    print("The values table should now be updated with current DMX values.")
    print()
    print("IMPORTANT:")
    print("The change detection will block further updates of the same values.")
    print("To see continuous live updates, you need to either:")
    print()
    print("Option A: Change DMX values in Eos (then they will update)")
    print("Option B: Run this script repeatedly (clears cache each time)")
    print("Option C: Disable change detection permanently (see below)")
    print()
    print("=" * 80)

print()
print("To DISABLE change detection permanently, edit dispatcher.py:")
print("Comment out lines 73-74 in dispatcher.py:")
print()
print("  # if prev.get(key) == val:")
print("  #     continue")
print()
print("This will update the table every frame, regardless of changes.")
print("=" * 80)
