"""Check the DMX input configuration."""

print("=" * 60)
print("DMX INPUT CONFIGURATION CHECK")
print("=" * 60)

# Find the DMX input CHOP
uni16 = op('/project1/io/EOS_Universe_016')

if not uni16:
    print("❌ ERROR: Cannot find /project1/io/EOS_Universe_016")
else:
    print(f"✅ Found DMX CHOP: {uni16}")
    print(f"   Type: {uni16.type}")
    print(f"   OPType: {uni16.OPType}")
    print(f"   Channels: {uni16.numChans}")
    print(f"   Samples: {uni16.numSamples}")
    print()

    # Check what kind of CHOP it is
    if hasattr(uni16, 'inputs') and uni16.inputs:
        print(f"   Has {len(uni16.inputs)} input(s):")
        for i, inp in enumerate(uni16.inputs):
            print(f"     Input {i}: {inp}")
            print(f"       Type: {inp.type if inp else 'None'}")
    else:
        print("   No inputs (might be a network receive CHOP)")

    print()

    # Check relevant parameters
    print("   Parameters:")
    for param_name in ['active', 'universe', 'port', 'network', 'protocol']:
        if hasattr(uni16.par, param_name):
            param = getattr(uni16.par, param_name)
            print(f"     {param_name}: {param.eval()}")

    print()

    # Show current channel values
    print("   Current channel values (first 20):")
    for i in range(min(20, uni16.numChans)):
        val = uni16[i].eval()
        if val != 0:  # Only show non-zero
            print(f"     Ch{i+1}: {val}")

    print()

# Look for other potential DMX sources
print("=" * 60)
print("Searching for other DMX-related OPs...")
print("=" * 60)

# Search in /project1/io/
io_comp = op('/project1/io')
if io_comp:
    print(f"Contents of {io_comp}:")
    for child in io_comp.children:
        if 'dmx' in child.name.lower() or 'sacn' in child.name.lower() or 'eos' in child.name.lower():
            print(f"  - {child.path}")
            print(f"    Type: {child.type}")
            if child.isCHOP:
                print(f"    Channels: {child.numChans}")

print()
print("=" * 60)
print("RECOMMENDATION:")
print("=" * 60)
print("1. Check if the DMX input CHOP is:")
print("   - 'active' parameter = True (enabled)")
print("   - Correct Universe = 16")
print("   - Correct network interface selected")
print("   - sACN data is actually arriving (check with Wireshark)")
print()
print("2. In TouchDesigner, open the DMX CHOP viewer:")
print("   - Click on the CHOP to select it")
print("   - Press 'V' to open the viewer")
print("   - Change values in Eos and see if they update")
print()
print("3. If it's a network receive CHOP (sACN), check:")
print("   - Firewall isn't blocking multicast")
print("   - Network interface is correct")
print("   - Eos is sending to correct IP/Universe")
print("=" * 60)
