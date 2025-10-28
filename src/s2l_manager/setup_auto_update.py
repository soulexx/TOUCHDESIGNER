"""Setup automatic DMX updates - make frame_tick run every frame."""

import sys
import importlib

print("=" * 60)
print("SETUP AUTOMATIC DMX → VALUES UPDATE")
print("=" * 60)

# 1. Reload all modules
print("Step 1: Reloading modules...")

sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)

manager_path = 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager'
if manager_path not in sys.path:
    sys.path.insert(0, manager_path)

import sacn_dispatch
importlib.reload(sacn_dispatch)
print("  ✅ sacn_dispatch reloaded")

import dispatcher
importlib.reload(dispatcher)
print("  ✅ dispatcher reloaded")

import audio_eos_mapper
importlib.reload(audio_eos_mapper)
print("  ✅ audio_eos_mapper reloaded")

print()

# 2. Clear cache and sync current DMX values
print("Step 2: Syncing current DMX values...")

sacn_dispatch._instances_cache.clear()

uni16 = op('/project1/io/EOS_Universe_016')
if uni16:
    # Convert to bytes
    data = []
    for channel in uni16.chans():
        raw = channel[0]
        value = max(0.0, min(255.0, raw))
        data.append(int(round(value)))

    if len(data) > 512:
        data = data[-512:]
    elif len(data) < 512:
        data.extend([0] * (512 - len(data)))

    payload = bytes(data)

    # Trigger once to populate
    sacn_dispatch.handle_universe(payload, 16)
    print(f"  ✅ Populated values table with current DMX")

    # Show current values
    print(f"  DMX Ch11 (Sensitivity): {uni16[10].eval()}")
    print(f"  DMX Ch12 (Threshold):   {uni16[11].eval()}")

print()

# 3. Build audio_params_table
print("Step 3: Building audio_params_table...")

audio_params_exec = op('/project1/src/s2l_manager/audio_params_exec')
if audio_params_exec:
    exec(audio_params_exec.text)
    if 'build_table' in dir():
        build_table()
        print("  ✅ audio_params_table built")

        audio_params = op('/project1/src/s2l_manager/audio_params_table')
        if audio_params and audio_params.numRows > 1:
            inst = audio_params[1, 0].val
            sens = audio_params[1, 1].val
            thresh = audio_params[1, 2].val
            print(f"  {inst}: Sensitivity={sens}, Threshold={thresh}")

print()

# 4. Check frame_tick configuration
print("Step 4: Checking frame_tick...")

frame_tick = op('/project1/io/frame_tick')
if frame_tick:
    print(f"  ✅ frame_tick found: {frame_tick}")

    # Check if it's configured as Execute DAT
    if hasattr(frame_tick.par, 'framestart'):
        is_enabled = frame_tick.par.framestart.eval()
        print(f"  Frame Start enabled: {is_enabled}")

        if not is_enabled:
            print("  ⚠️  WARNING: frame_tick Frame Start is NOT enabled!")
            print("     To enable automatic updates:")
            print("     1. Select /project1/io/frame_tick")
            print("     2. In parameter panel → DAT Execute")
            print("     3. Check 'Frame Start'")
    else:
        print("  ⚠️  frame_tick doesn't have 'framestart' parameter")
        print("     Make sure it's configured as Execute DAT")

print()

# 5. Test OSC output
print("Step 5: Testing OSC output...")

osc_out = op('/project1/io/oscout1')
if osc_out:
    print(f"  ✅ OSC out found: {osc_out}")

    # Send a test message to Sub 11
    try:
        osc_out.sendOSC('/eos/sub/11', [0.5])
        print("  ✅ Test OSC sent to Sub 11 at 50%")
    except Exception as e:
        print(f"  ❌ Error sending OSC: {e}")
else:
    print("  ❌ OSC output not found at /project1/io/oscout1")

print()
print("=" * 60)
print("SETUP COMPLETE")
print("=" * 60)
print()
print("TO ENABLE AUTOMATIC UPDATES:")
print("1. Make sure frame_tick has 'Frame Start' enabled in Execute DAT")
print("2. Change DMX values in Eos")
print("3. Watch the textport for [s2l_manager] logs")
print("4. The subs should update automatically")
print()
print("TO TEST MANUALLY (if frame_tick is not running):")
print("Run this every time you change Eos values:")
print("  exec(open('C:/_DEV/TOUCHDESIGNER/src/s2l_manager/test_direct_handle_universe.py').read())")
print("=" * 60)
