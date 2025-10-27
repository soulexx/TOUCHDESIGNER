"""Find OSC In and OSC Out operators in the project."""

base = op('/project1')

print("\n=== SEARCHING FOR OSC OPERATORS ===\n")

# Search for OSC In
print("OSC In DATs:")
oscin_ops = base.findChildren(type=CHOP, name="oscin*") + base.findChildren(type=DAT, name="oscin*")
for o in oscin_ops:
    print(f"  {o.path} (type: {o.OPType})")

# Search for OSC Out
print("\nOSC Out CHOPs:")
oscout_ops = base.findChildren(type=CHOP, name="oscout*")
for o in oscout_ops:
    print(f"  {o.path}")
    if hasattr(o.par, 'address'):
        print(f"    Address: {o.par.address}")
        print(f"    Port: {o.par.port}")

# Check what state module uses
print("\n=== CHECKING STATE MODULE ===")
try:
    state_mod = mod('/project1/palette_logic/state')
    osc = state_mod.get_osc_out()
    if osc:
        print(f"State module OSC Out: {osc.path}")
        if hasattr(osc.par, 'address'):
            print(f"  Address: {osc.par.address}")
            print(f"  Port: {osc.par.port}")
    else:
        print("State module OSC Out: None")
except Exception as e:
    print(f"Error: {e}")

print("\n=== END SEARCH ===\n")
