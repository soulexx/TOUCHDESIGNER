"""Force enable frame_tick Execute parameters."""

print("=" * 60)
print("FIX FRAME_TICK EXECUTE")
print("=" * 60)
print()

frame_tick = op('/project1/io/frame_tick')

if not frame_tick:
    print("❌ frame_tick not found")
else:
    print(f"✅ frame_tick: {frame_tick}")
    print()

    # List all parameters that might be relevant
    print("Checking Execute parameters...")
    print()

    par_dict = {}

    # Check common execute parameter names
    possible_params = [
        'framestart', 'frame', 'executeframestart',
        'onframestart', 'active', 'enable'
    ]

    for param_name in possible_params:
        if hasattr(frame_tick.par, param_name):
            param = getattr(frame_tick.par, param_name)
            value = param.eval()
            par_dict[param_name] = (param, value)
            print(f"  {param_name}: {value}")

    print()

    # Try to enable frame start
    if 'framestart' in par_dict:
        param, current_value = par_dict['framestart']
        print(f"Setting framestart to True (currently: {current_value})")
        try:
            frame_tick.par.framestart = True
            print("  ✅ Set to True")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    else:
        print("⚠️  No 'framestart' parameter found!")
        print()
        print("This means the DAT is not an Execute DAT.")
        print()
        print("MANUAL FIX REQUIRED:")
        print("1. In TouchDesigner, select /project1/io/frame_tick")
        print("2. Right-click → Parameters → Customize Component Interface")
        print("3. OR: Delete it and create a new 'Execute DAT'")
        print("4. In the parameter panel, look for 'DAT Execute' section")
        print("5. Enable 'Frame Start'")

    print()
    print("=" * 60)
    print("ALTERNATIVE: Use audio_eos_exec's onFrameStart")
    print("=" * 60)
    print()
    print("Since audio_eos_exec IS running (subs are moving),")
    print("we can add the DMX update logic there instead!")
    print()
    print("Would you like me to:")
    print("A) Help you fix frame_tick manually")
    print("B) Move the DMX logic into audio_eos_exec (simpler)")
    print("=" * 60)
