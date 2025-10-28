"""Sync current DMX values to tables by triggering frame_tick."""

import sys
import importlib

# Ensure modules are loaded
sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)

import sacn_dispatch
importlib.reload(sacn_dispatch)

manager_path = 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager'
if manager_path not in sys.path:
    sys.path.insert(0, manager_path)

import dispatcher
importlib.reload(dispatcher)

print("=" * 60)
print("SYNCING DMX TO TABLES")
print("=" * 60)

# Read current DMX values
uni16 = op('/project1/io/EOS_Universe_016')
if not uni16:
    print("❌ ERROR: DMX CHOP not found")
else:
    print(f"✅ Current DMX values:")
    print(f"   Ch11 (Sensitivity): {uni16[10].eval()}")
    print(f"   Ch12 (Threshold):   {uni16[11].eval()}")
    print(f"   Ch13 (LowCut_Hz):   {uni16[12].eval()}")
    print()

    # Clear values table
    values = op('/project1/src/s2l_manager/values')
    if values:
        values.clear()
        values.appendRow(['instance', 'parameter', 'value'])
        print("✅ Cleared values table")

    # Manually trigger frame_tick to update from current DMX
    print("✅ Triggering frame_tick...")

    frame_tick = op('/project1/io/frame_tick')
    if frame_tick:
        # Execute frame_tick code
        exec(frame_tick.text)
        if 'onFrameStart' in dir():
            onFrameStart(frame_tick)
            print("✅ frame_tick executed")
        else:
            print("❌ onFrameStart not found")

    print()
    print("=" * 60)
    print("AFTER SYNC:")
    print("=" * 60)

    # Check values table
    if values:
        print(f"values table rows: {values.numRows}")
        for r in range(1, min(10, values.numRows)):
            inst = values[r, 0].val
            param = values[r, 1].val
            value = values[r, 2].val
            if inst == 'S2L_UNIT_1' and param in ['Sensitivity', 'Threshold', 'LowCut_Hz']:
                print(f"  {inst}:{param} = {value}")

    print()

    # Trigger audio_params rebuild
    audio_params_exec = op('/project1/src/s2l_manager/audio_params_exec')
    if audio_params_exec:
        print("✅ Rebuilding audio_params_table...")
        exec(audio_params_exec.text)
        if 'build_table' in dir():
            build_table()

        # Check result
        audio_params = op('/project1/src/s2l_manager/audio_params_table')
        if audio_params and audio_params.numRows > 1:
            inst = audio_params[1, 0].val
            sens = audio_params[1, 1].val
            thresh = audio_params[1, 2].val
            lowcut = audio_params[1, 3].val
            print(f"audio_params_table: {inst}")
            print(f"  Sensitivity: {sens}")
            print(f"  Threshold:   {thresh}")
            print(f"  LowCut_Hz:   {lowcut}")

    print()
    print("=" * 60)
    print("NOW TEST: Change a value in Eos and run this script again!")
    print("The values should update automatically if frame_tick is running.")
    print("=" * 60)
