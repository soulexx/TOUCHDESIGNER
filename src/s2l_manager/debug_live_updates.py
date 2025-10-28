"""Debug why values don't update when changing in Eos."""

import time

print("=" * 60)
print("LIVE UPDATE DEBUG")
print("=" * 60)

# Check current DMX values
uni16 = op('/project1/io/EOS_Universe_016')
if uni16:
    ch11 = uni16[10].eval()
    ch12 = uni16[11].eval()
    ch13 = uni16[12].eval()
    print(f"Current DMX values:")
    print(f"  Channel 11 (Sensitivity): {ch11}")
    print(f"  Channel 12 (Threshold):   {ch12}")
    print(f"  Channel 13 (LowCut_Hz):   {ch13}")
else:
    print("ERROR: DMX CHOP not found")

print()

# Check values table
values = op('/project1/src/s2l_manager/values')
if values:
    # Find S2L_UNIT_1 Sensitivity row
    for r in range(1, values.numRows):
        inst = values[r, 0].val
        param = values[r, 1].val
        value = values[r, 2].val
        if inst == 'S2L_UNIT_1' and param in ['Sensitivity', 'Threshold', 'LowCut_Hz']:
            print(f"values table: {inst}:{param} = {value}")
else:
    print("ERROR: values table not found")

print()

# Check audio_params_table
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
else:
    print("ERROR: audio_params_table empty")

print()
print("=" * 60)
print("Now change a value in Eos (e.g. Channel 11 Sensitivity)")
print("Wait 2 seconds, then the script will check again...")
print("=" * 60)

# Wait for user to change value
time.sleep(2)

print()
print("AFTER CHANGE:")
print("=" * 60)

# Check DMX again
if uni16:
    ch11_new = uni16[10].eval()
    ch12_new = uni16[11].eval()
    ch13_new = uni16[12].eval()
    print(f"DMX values NOW:")
    print(f"  Channel 11: {ch11} → {ch11_new} {'✅ CHANGED' if ch11 != ch11_new else '❌ NO CHANGE'}")
    print(f"  Channel 12: {ch12} → {ch12_new} {'✅ CHANGED' if ch12 != ch12_new else '❌ NO CHANGE'}")
    print(f"  Channel 13: {ch13} → {ch13_new} {'✅ CHANGED' if ch13 != ch13_new else '❌ NO CHANGE'}")

print()

# Check values table again
if values:
    for r in range(1, values.numRows):
        inst = values[r, 0].val
        param = values[r, 1].val
        value = values[r, 2].val
        if inst == 'S2L_UNIT_1' and param in ['Sensitivity', 'Threshold', 'LowCut_Hz']:
            print(f"values table: {inst}:{param} = {value}")

print()

# Check if frame_tick is actually running
frame_tick = op('/project1/io/frame_tick')
if frame_tick:
    print(f"frame_tick DAT found: {frame_tick}")

    # Check if it has Execute parameters
    has_frame_start = hasattr(frame_tick.par, 'framestart')
    has_execute = hasattr(frame_tick.par, 'execute')

    print(f"  Has 'framestart' parameter: {has_frame_start}")
    print(f"  Has 'execute' parameter: {has_execute}")

    if has_frame_start:
        print(f"  framestart value: {frame_tick.par.framestart}")
    if has_execute:
        print(f"  execute value: {frame_tick.par.execute}")

    # Try to manually call it
    print()
    print("Manually calling frame_tick.onFrameStart()...")
    try:
        # Execute the frame_tick code
        exec(frame_tick.text)
        if 'onFrameStart' in dir():
            onFrameStart(frame_tick)
            print("  ✅ Manual call succeeded")
        else:
            print("  ❌ onFrameStart function not found")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print()
print("=" * 60)
print("Check values table one more time after manual trigger:")

if values:
    for r in range(1, values.numRows):
        inst = values[r, 0].val
        param = values[r, 1].val
        value = values[r, 2].val
        if inst == 'S2L_UNIT_1' and param in ['Sensitivity', 'Threshold', 'LowCut_Hz']:
            print(f"  {inst}:{param} = {value}")

print("=" * 60)
