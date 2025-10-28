"""
Paste this DIRECTLY into the TouchDesigner Textport.
This will find your audio_analysis and audio_params_table operators.
"""

print("\n" + "="*60)
print("AUDIO-EOS OPERATOR FINDER")
print("="*60)

# Find audio_analysis
print("\n1. Looking for 'audio_analysis' operators:")
audio_ops = root.findChildren(name='audio_analysis')
if audio_ops:
    for ao in audio_ops:
        print(f"   Found: {ao.path}")
        print(f"   Type:  {ao.type}")
        # Check if it has audio channels
        if hasattr(ao, 'numChans') and ao.numChans > 0:
            print(f"   Channels: {ao.numChans}")
            chans = [ao[i].name for i in range(min(10, ao.numChans))]
            print(f"   Sample channels: {', '.join(chans)}")
else:
    print("   ❌ NOT FOUND")
    print("\n   Searching for audio-related CHOPs:")
    audio_related = root.findChildren(type='audiospectrum') + root.findChildren(type='audioband')
    for ao in audio_related[:5]:
        print(f"      {ao.path} ({ao.type})")

# Find audio_params_table
print("\n2. Looking for 'audio_params_table' operators:")
params_ops = root.findChildren(name='audio_params_table')
if params_ops:
    for po in params_ops:
        print(f"   Found: {po.path}")
        print(f"   Type:  {po.type}")
        if hasattr(po, 'numRows'):
            print(f"   Rows: {po.numRows}, Cols: {po.numCols}")
            if po.numRows > 0:
                headers = [po[0, i].val for i in range(min(7, po.numCols))]
                print(f"   Headers: {headers}")
else:
    print("   ❌ NOT FOUND")
    print("\n   Searching for tables with 'param' or 's2l':")
    param_tables = root.findChildren(name='*param*') + root.findChildren(name='*s2l*')
    for pt in param_tables[:5]:
        if pt.type in ['table', 'text']:
            print(f"      {pt.path} ({pt.type})")

# Find values table (from dispatcher)
print("\n3. Looking for 'values' table (S2L dispatcher):")
values_ops = root.findChildren(name='values')
s2l_values = [v for v in values_ops if 's2l' in v.path.lower()]
if s2l_values:
    for vo in s2l_values[:3]:
        print(f"   Found: {vo.path}")
else:
    print("   ❌ NOT FOUND (this is optional)")

# Find OSC output
print("\n4. Looking for OSC output:")
try:
    osc_op = op('/project1/io/oscout1')
    print(f"   ✓ Found: {osc_op.path} ({osc_op.type})")
except:
    print("   ❌ NOT FOUND at /project1/io/oscout1")
    print("\n   Searching for OSC operators:")
    osc_ops = root.findChildren(type='oscout')
    for oo in osc_ops[:5]:
        print(f"      {oo.path}")

print("\n" + "="*60)
print("RECOMMENDED SETUP:")
print("="*60)

if audio_ops:
    audio_path = audio_ops[0].path
    print(f"\n✓ audio_analysis found at: {audio_path}")
    print(f"  Use in audio_eos_exec.py:")
    print(f"    audio_analysis = op('{audio_path}')")
else:
    print("\n❌ audio_analysis NOT FOUND")
    print("  Create an Audio Analysis CHOP or check the name")

if params_ops:
    params_path = params_ops[0].path
    print(f"\n✓ audio_params_table found at: {params_path}")
    print(f"  Use in audio_eos_exec.py:")
    print(f"    audio_params = op('{params_path}')")
else:
    print("\n❌ audio_params_table NOT FOUND")
    print("  This should be created by audio_params_exec.py")
    print("  Check if the table is named differently")

print("\n" + "="*60)
print("\nNext steps:")
print("1. Copy the op() paths above")
print("2. Edit: C:/_DEV/TOUCHDESIGNER/src/s2l_manager/audio_eos_exec.py")
print("3. Update lines 45-46 with the correct paths")
print("="*60 + "\n")

# Test reading values if operators found
if audio_ops:
    print("\n" + "="*60)
    print("TESTING AUDIO VALUES:")
    print("="*60)
    ao = audio_ops[0]
    test_channels = ['low', 'mid', 'high', 'kick', 'snare', 'rhythm']
    print(f"\nReading from: {ao.path}\n")
    for chan_name in test_channels:
        try:
            chan = ao[chan_name]
            if chan:
                val = chan.eval()
                print(f"  {chan_name:15s}: {val:.4f}")
            else:
                # Channel doesn't exist
                pass
        except:
            pass
    print("\nIf you see values above, audio analysis is working! ✓")
    print("="*60 + "\n")
