"""
Helper script to find the correct operator paths for audio_eos mapping.
Run this in TouchDesigner Textport to find your operators.

Usage:
    import sys
    sys.path.append('C:/_DEV/TOUCHDESIGNER/src/s2l_manager')
    import find_operators
    find_operators.find_all()
"""

# Import TouchDesigner's op from root
try:
    import __main__
    if hasattr(__main__, 'op'):
        op = __main__.op
    else:
        # Try to get it from the module scope
        import builtins
        if hasattr(builtins, 'op'):
            op = builtins.op
        else:
            op = None
except:
    op = None

def find_all():
    """Find all required operators and print their paths."""
    global op

    # Try to get op from TouchDesigner if not already available
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            print("ERROR: Cannot access TouchDesigner 'op' object")
            print("Make sure you're running this from TouchDesigner Textport!")
            return

    print("\n" + "="*60)
    print("AUDIO-EOS OPERATOR FINDER")
    print("="*60)

    # Find audio_analysis
    print("\n1. Looking for 'audio_analysis' operators:")
    try:
        audio_ops = [o for o in root.findChildren(name='audio_analysis')]  # type: ignore[name-defined]
    except:
        audio_ops = []
    if audio_ops:
        for ao in audio_ops:
            print(f"   Found: {ao.path}")
            print(f"   Type:  {ao.type}")
            # Check if it has audio channels
            if hasattr(ao, 'numChans'):
                print(f"   Channels: {ao.numChans}")
                if ao.numChans > 0:
                    chans = [ao[i].name for i in range(min(10, ao.numChans))]
                    print(f"   First channels: {', '.join(chans)}")
    else:
        print("   ❌ NOT FOUND")
        print("   Try searching for similar names:")
        # Search for audio-related CHOPs
        audio_related = op.find('*audio*')  # type: ignore[name-defined]
        for ao in audio_related[:5]:  # First 5 results
            if ao.type in ['audiospectrum', 'audioband', 'audioanalysis', 'null']:
                print(f"      {ao.path} ({ao.type})")

    # Find audio_params_table
    print("\n2. Looking for 'audio_params_table' operators:")
    params_ops = op.find('audio_params_table')  # type: ignore[name-defined]
    if params_ops:
        for po in params_ops:
            print(f"   Found: {po.path}")
            print(f"   Type:  {po.type}")
            # Check if it has rows
            if hasattr(po, 'numRows'):
                print(f"   Rows: {po.numRows}")
                if po.numRows > 0:
                    print(f"   First row: {[po[0, i].val for i in range(min(5, po.numCols))]}")
    else:
        print("   ❌ NOT FOUND")
        print("   Try searching for S2L parameter tables:")
        param_tables = op.find('*param*')  # type: ignore[name-defined]
        for pt in param_tables[:5]:
            if pt.type in ['table', 'text']:
                print(f"      {pt.path} ({pt.type})")

    # Find OSC output
    print("\n3. Looking for OSC output:")
    osc_op = op('/project1/io/oscout1')  # type: ignore[name-defined]
    if osc_op:
        print(f"   Found: {osc_op.path}")
        print(f"   Type:  {osc_op.type}")
    else:
        print("   ❌ NOT FOUND at /project1/io/oscout1")
        print("   Searching for OSC operators:")
        osc_ops = op.find('*osc*')  # type: ignore[name-defined]
        for oo in osc_ops[:5]:
            if 'out' in oo.name.lower():
                print(f"      {oo.path} ({oo.type})")

    # Find execute location (where to put audio_eos_exec)
    print("\n4. Looking for s2l_manager location:")
    s2l_managers = op.find('*s2l*manager*')  # type: ignore[name-defined]
    if s2l_managers:
        for sm in s2l_managers[:3]:
            print(f"   Found: {sm.path} ({sm.type})")

    print("\n" + "="*60)
    print("RECOMMENDED PATHS:")
    print("="*60)

    if audio_ops:
        audio_path = audio_ops[0].path
        print(f"\naudio_analysis = op('{audio_path}')")
    else:
        print("\naudio_analysis = op('???')  # NOT FOUND - Check manually")

    if params_ops:
        params_path = params_ops[0].path
        print(f"audio_params = op('{params_path}')")
    else:
        print("audio_params = op('???')  # NOT FOUND - Check manually")

    print("\n" + "="*60)
    print("\nNext steps:")
    print("1. Copy the paths above")
    print("2. Edit audio_eos_exec.py")
    print("3. Replace the operator paths (lines ~38-39)")
    print("="*60 + "\n")


def find_from_execute(exec_op):
    """
    Find operators relative to an Execute DAT location.

    Usage:
        import find_operators
        exec_dat = op('/project1/s2l_audio/audio_eos_exec')
        find_operators.find_from_execute(exec_dat)
    """
    print(f"\nSearching from Execute DAT: {exec_op.path}")
    print("="*60)

    # Try common relative paths
    relative_paths = [
        ('../../s2l_audio/fixtures/audio_analysis', 'audio_analysis'),
        ('../audio_analysis', 'audio_analysis'),
        ('audio_analysis', 'audio_analysis'),
        ('/project1/s2l_audio/fixtures/audio_analysis', 'audio_analysis'),

        ('../audio_params_table', 'audio_params_table'),
        ('audio_params_table', 'audio_params_table'),
        ('/project1/s2l_manager/audio_params_table', 'audio_params_table'),
    ]

    found = {}

    for rel_path, name in relative_paths:
        try:
            test_op = exec_op.op(rel_path)  # type: ignore[attr-defined]
            if test_op:
                print(f"✓ Found {name}: {rel_path}")
                found[name] = rel_path
                break
        except:
            pass

    print("\n" + "="*60)
    if found:
        print("Use these relative paths in audio_eos_exec.py:")
        for name, path in found.items():
            print(f"  {name} = op('{path}')")
    else:
        print("Could not find operators with relative paths.")
        print("Use absolute paths instead (run find_all() to get them)")
    print("="*60 + "\n")


def test_mapping():
    """Quick test to see if mapping would work."""
    print("\n" + "="*60)
    print("TESTING AUDIO MAPPING")
    print("="*60)

    # Find operators
    audio_ops = op.find('audio_analysis')  # type: ignore[name-defined]
    params_ops = op.find('audio_params_table')  # type: ignore[name-defined]

    if not audio_ops:
        print("❌ Cannot test: audio_analysis not found")
        return

    if not params_ops:
        print("❌ Cannot test: audio_params_table not found")
        return

    audio_op = audio_ops[0]
    params_op = params_ops[0]

    print(f"\n✓ Using audio_analysis: {audio_op.path}")
    print(f"✓ Using audio_params_table: {params_op.path}")

    # Test reading audio values
    print("\nAudio values:")
    test_channels = ['low', 'mid', 'high', 'kick', 'snare', 'rhythm']
    for chan_name in test_channels:
        try:
            chan = audio_op[chan_name]
            if chan:
                val = chan.eval()
                print(f"  {chan_name}: {val:.3f}")
            else:
                print(f"  {chan_name}: NOT FOUND")
        except:
            print(f"  {chan_name}: ERROR")

    # Test reading params
    print("\nS2L Parameters:")
    try:
        for row in range(1, min(4, params_op.numRows)):
            instance = params_op[row, 0].val
            sensitivity = params_op[row, 1].val if params_op.numCols > 1 else '?'
            threshold = params_op[row, 2].val if params_op.numCols > 2 else '?'
            print(f"  {instance}: Sensitivity={sensitivity}, Threshold={threshold}")
    except Exception as e:
        print(f"  ERROR reading params: {e}")

    print("\n" + "="*60)
    print("If you see values above, the mapping should work!")
    print("="*60 + "\n")


# Auto-run when imported interactively
if __name__ != '__main__':
    print("\n💡 Tip: Run find_operators.find_all() to search for operators")
