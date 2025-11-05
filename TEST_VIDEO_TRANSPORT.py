# Complete Video Transport System Test

print("="*70)
print("VIDEO TRANSPORT SYSTEM TEST")
print("="*70)

# Get all CHOPs
fader_input = op('/project1/media/fader_input')
transport = op('/project1/media/transport_control')
math1 = op('/project1/media/math1')
count_auto = op('/project1/media/count_auto')
limit1 = op('/project1/media/limit1')
switch2 = op('/project1/media/switch2')
filter1 = op('/project1/media/filter1')
movie = op('/project1/media/moviefilein1')

print("\n[1] CHECKING ALL CHOPs EXIST:")
print("-" * 70)
components = {
    'fader_input': fader_input,
    'transport_control': transport,
    'math1': math1,
    'count_auto': count_auto,
    'limit1': limit1,
    'switch2': switch2,
    'filter1': filter1,
    'moviefilein1': movie
}

all_exist = True
for name, op_ref in components.items():
    exists = op_ref is not None
    status = "✓" if exists else "✗"
    print(f"  {status} {name}: {op_ref.path if exists else 'NOT FOUND'}")
    if not exists:
        all_exist = False

if not all_exist:
    print("\n[ERROR] Missing CHOPs! Run FIX_PLAY_STOP.py first!")
    exit()

print("\n[2] CHECKING CONNECTIONS:")
print("-" * 70)

# Check math1 connections
if math1:
    math1_input = math1.inputs[0] if len(math1.inputs) > 0 else None
    print(f"  math1 input 0: {math1_input.path if math1_input else 'NONE'}")
    if math1_input == fader_input:
        print("    ✓ Correctly connected to fader_input")
    else:
        print("    ✗ WRONG! Should be fader_input")

# Check limit1 connections
if limit1:
    limit1_input = limit1.inputs[0] if len(limit1.inputs) > 0 else None
    print(f"  limit1 input 0: {limit1_input.path if limit1_input else 'NONE'}")
    if limit1_input == count_auto:
        print("    ✓ Correctly connected to count_auto")
    else:
        print("    ✗ WRONG! Should be count_auto")

# Check switch2 connections
if switch2:
    switch2_input0 = switch2.inputs[0] if len(switch2.inputs) > 0 else None
    switch2_input1 = switch2.inputs[1] if len(switch2.inputs) > 1 else None
    print(f"  switch2 input 0 (auto-play): {switch2_input0.path if switch2_input0 else 'NONE'}")
    print(f"  switch2 input 1 (scrub): {switch2_input1.path if switch2_input1 else 'NONE'}")
    if switch2_input0 == limit1:
        print("    ✓ Input 0 correctly connected to limit1 (auto-play)")
    else:
        print("    ✗ Input 0 WRONG! Should be limit1")
    if switch2_input1 == math1:
        print("    ✓ Input 1 correctly connected to math1 (scrub)")
    else:
        print("    ✗ Input 1 WRONG! Should be math1")

# Check filter1 connections
if filter1:
    filter1_input = filter1.inputs[0] if len(filter1.inputs) > 0 else None
    print(f"  filter1 input 0: {filter1_input.path if filter1_input else 'NONE'}")
    if filter1_input == switch2:
        print("    ✓ Correctly connected to switch2")
    else:
        print("    ✗ WRONG! Should be switch2")

print("\n[3] CHECKING CURRENT VALUES:")
print("-" * 70)

if fader_input:
    print(f"  fader_input['normalized'] = {fader_input['normalized'].eval()}")

if transport:
    print(f"  transport['playing'] = {transport['playing'].eval()}")
    print(f"  transport['scrubbing'] = {transport['scrubbing'].eval()}")

if math1 and math1.numChans > 0:
    print(f"  math1[0] = {math1[0].eval()} (scaled to frames)")

if count_auto and count_auto.numChans > 0:
    print(f"  count_auto[0] = {count_auto[0].eval()}")

if limit1 and limit1.numChans > 0:
    print(f"  limit1[0] = {limit1[0].eval()}")

if switch2 and switch2.numChans > 0:
    print(f"  switch2[0] = {switch2[0].eval()}")
    print(f"  switch2.par.index = {switch2.par.index.eval()}")

if filter1 and filter1.numChans > 0:
    print(f"  filter1[0] = {filter1[0].eval()}")

if movie:
    print(f"  movie.par.index = {movie.par.index.eval()}")
    print(f"  movie.par.index.mode = {movie.par.index.mode}")

print("\n[4] INTERACTIVE TESTS:")
print("-" * 70)
print("\nTest Scrubbing (move fader):")
print("  op('/project1/media/fader_input')['normalized'].val = 0.25")
print("  op('/project1/media/transport_control')['scrubbing'].val = 1")

print("\nTest Play:")
print("  op('/project1/media/transport_control')['playing'].val = 1")
print("  op('/project1/media/transport_control')['scrubbing'].val = 0")

print("\nTest Stop:")
print("  op('/project1/media/transport_control')['playing'].val = 0")
print("  op('/project1/media/transport_control')['scrubbing'].val = 1")
print("  op('/project1/media/count_auto').par.count = 0")

print("\n" + "="*70)
print("SYSTEM STATUS:")
print("="*70)

# Overall health check
scrubbing_works = (
    fader_input and transport and math1 and switch2 and filter1 and movie
    and len(math1.inputs) > 0 and math1.inputs[0] == fader_input
    and len(switch2.inputs) > 1 and switch2.inputs[1] == math1
    and len(filter1.inputs) > 0 and filter1.inputs[0] == switch2
)

autoplay_works = (
    count_auto and limit1 and switch2
    and len(limit1.inputs) > 0 and limit1.inputs[0] == count_auto
    and len(switch2.inputs) > 0 and switch2.inputs[0] == limit1
)

if scrubbing_works:
    print("✓ SCRUBBING: Ready")
else:
    print("✗ SCRUBBING: BROKEN - check connections above")

if autoplay_works:
    print("✓ AUTO-PLAY: Ready")
else:
    print("✗ AUTO-PLAY: BROKEN - check connections above")

print("\n" + "="*70)
