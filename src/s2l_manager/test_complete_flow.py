"""Test the complete DMX → Audio → OSC flow."""

print("=" * 60)
print("COMPLETE FLOW TEST")
print("=" * 60)

# 1. Check DMX input
uni16 = op('/project1/io/EOS_Universe_016')
if uni16:
    ch11 = uni16[10].eval()
    ch12 = uni16[11].eval()
    print("✅ Step 1: DMX Input")
    print(f"   Ch11 (Sensitivity): {ch11}")
    print(f"   Ch12 (Threshold):   {ch12}")
else:
    print("❌ Step 1: DMX Input FAILED")

print()

# 2. Check values table
values = op('/project1/src/s2l_manager/values')
if values and values.numRows > 1:
    print(f"✅ Step 2: values table ({values.numRows} rows)")
    for r in range(1, values.numRows):
        inst = values[r, 0].val
        param = values[r, 1].val
        val = values[r, 2].val
        if inst == 'S2L_UNIT_1' and param in ['Sensitivity', 'Threshold']:
            print(f"   {inst}:{param} = {val}")
else:
    print("❌ Step 2: values table EMPTY")

print()

# 3. Rebuild audio_params_table
audio_params_exec = op('/project1/src/s2l_manager/audio_params_exec')
if audio_params_exec:
    exec(audio_params_exec.text)
    if 'build_table' in dir():
        build_table()

audio_params = op('/project1/src/s2l_manager/audio_params_table')
if audio_params and audio_params.numRows > 1:
    inst = audio_params[1, 0].val
    sens = audio_params[1, 1].val
    thresh = audio_params[1, 2].val
    print(f"✅ Step 3: audio_params_table")
    print(f"   {inst}: Sensitivity={sens}, Threshold={thresh}")
else:
    print("❌ Step 3: audio_params_table EMPTY")

print()

# 4. Check audio analysis
audio_analysis = op('/project1/s2l_audio/fixutres/audio_analysis')
if audio_analysis:
    # Get a few channel values
    has_channels = False
    print("✅ Step 4: Audio Analysis")
    for ch_name in ['low', 'mid', 'high', 'kick']:
        try:
            ch = audio_analysis[ch_name]
            val = ch[0]
            print(f"   {ch_name}: {val:.3f}")
            has_channels = True
        except:
            pass
    if not has_channels:
        print("   (No audio channels found)")
else:
    print("❌ Step 4: Audio Analysis NOT FOUND")

print()

# 5. Test audio_eos_mapper
print("✅ Step 5: Testing audio_eos_mapper")

import sys
manager_path = 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager'
if manager_path not in sys.path:
    sys.path.insert(0, manager_path)

try:
    import audio_eos_mapper
    import importlib
    importlib.reload(audio_eos_mapper)

    # Test with sample values
    print("   Testing _apply_s2l_params()...")

    # Test 1: Sensitivity only
    result1 = audio_eos_mapper._apply_s2l_params(
        raw_value=0.5,
        sensitivity=float(sens) if sens else 100.0,
        threshold=0.0,
        lowcut_hz=0.0,
        highcut_hz=0.0
    )
    print(f"   Raw 0.5 → {result1:.3f} (with sensitivity={sens})")

    # Test 2: Sensitivity + Threshold
    result2 = audio_eos_mapper._apply_s2l_params(
        raw_value=0.5,
        sensitivity=float(sens) if sens else 100.0,
        threshold=float(thresh) if thresh else 0.0,
        lowcut_hz=0.0,
        highcut_hz=0.0
    )
    print(f"   Raw 0.5 → {result2:.3f} (with sensitivity={sens}, threshold={thresh})")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print("The complete flow is:")
print("1. Eos sends DMX → Universe 16 → TouchDesigner")
print("2. frame_tick calls sacn_dispatch → dispatcher → values table")
print("3. audio_params_exec builds audio_params_table from values")
print("4. audio_eos_exec reads audio + params → sends OSC to Eos")
print()
print("Next step: Test that changing Sensitivity/Threshold in Eos")
print("affects the OSC output values!")
print("=" * 60)
