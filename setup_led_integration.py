"""
Automatic LED Integration for VPlayer
Connects vplayer LED output to existing driver_led.py system

Usage:
1. Open your TouchDesigner project
2. Make sure vplayer exists at /project1/media/vplayer
3. Run: exec(open('c:\\_DEV\\TOUCHDESIGNER\\setup_led_integration.py').read())

Author: Claude Code Agent
Version: 1.0
"""

print("=" * 80)
print("LED INTEGRATION AUTOMATIC SETUP")
print("=" * 80)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

VPLAYER_PATH = '/project1/media/vplayer'
LED_CONST_PATH = '/project1/io/led_const'  # Adjust if different
DRIVER_LED_PATH = '/project1/io/driver_led'  # Adjust if different

# ==============================================================================
# STEP 1: Find LED Components
# ==============================================================================

print("\n[1/4] Finding LED components...")

vplayer = op(VPLAYER_PATH)
led_const = op(LED_CONST_PATH)
driver_led = op(DRIVER_LED_PATH)

if not vplayer:
    print(f"  ERROR: vplayer not found at {VPLAYER_PATH}")
    print("  Please run build_vplayer.py first!")
else:
    print(f"  ✓ Found vplayer at {VPLAYER_PATH}")

if not led_const:
    print(f"  ⚠ LED Constant CHOP not found at {LED_CONST_PATH}")
    print("  Attempting to locate...")

    # Try common paths
    common_paths = [
        '/project1/io/led_const',
        '/project1/layers/leds/led_const',
        '/project1/leds/led_const'
    ]

    for path in common_paths:
        led_const = op(path)
        if led_const:
            LED_CONST_PATH = path
            print(f"  ✓ Found LED Constant at {LED_CONST_PATH}")
            break

    if not led_const:
        print(f"  ERROR: Could not find LED Constant CHOP")
        print(f"  Please update LED_CONST_PATH in script")
else:
    print(f"  ✓ Found LED Constant at {LED_CONST_PATH}")

if not driver_led:
    print(f"  ⚠ driver_led not found at {DRIVER_LED_PATH}")
    print("  This may be normal if LED system uses different structure")
else:
    print(f"  ✓ Found driver_led at {DRIVER_LED_PATH}")

# ==============================================================================
# STEP 2: Check VPlayer LED Output
# ==============================================================================

print("\n[2/4] Checking vplayer LED output...")

if vplayer:
    led_go_out = vplayer.op('led_go_out')
    if led_go_out and led_go_out.numChans > 0:
        current_value = led_go_out['btn_21'].eval()
        print(f"  ✓ VPlayer led_go_out exists")
        print(f"  ✓ Current LED value (btn_21): {current_value}")
    else:
        print(f"  ERROR: led_go_out not found or has no channels")
        print(f"  Please run build_vplayer.py first!")

# ==============================================================================
# STEP 3: Integrate with LED Constant
# ==============================================================================

print("\n[3/4] Integrating with LED Constant...")

if led_const and vplayer:
    # Check if btn_21 channel exists
    btn_21_exists = False
    for i in range(led_const.numChans):
        if 'btn_21' in led_const.chan(i).name or 'btn/21' in led_const.chan(i).name:
            btn_21_exists = True
            btn_21_index = i
            print(f"  ✓ Found existing btn_21 channel at index {i}")
            break

    if not btn_21_exists:
        print(f"  - btn_21 channel not found, will add instructions for manual addition")

    # Create helper Select CHOP for menu-aware switching
    if vplayer.op('led_menu_aware'):
        print(f"  - led_menu_aware already exists, skipping")
    else:
        led_menu_aware = vplayer.create(scriptCHOP, 'led_menu_aware')
        led_menu_aware_code = """# Menu-Aware LED Switcher
# Outputs vplayer LED only when Menu 5 is active

def cook(scriptOp):
    try:
        # Check active menu
        project = op('/project1')
        active_menu = project.fetch('ACTIVE_MENU', 0)

        # Get LED value
        led_out = op('../led_go_out')
        if not led_out or led_out.numChans == 0:
            return

        led_value = led_out['btn_21'].eval()

        # Only output if Menu 5 is active
        scriptOp.clear()
        if active_menu == 5:
            scriptOp.numChans = 1
            scriptOp[0].name = 'btn_21_vplayer'
            scriptOp[0] = led_value
        else:
            # Output 0 when not active (let Eos control take over)
            scriptOp.numChans = 1
            scriptOp[0].name = 'btn_21_vplayer'
            scriptOp[0] = 0

    except Exception as e:
        pass  # Suppress errors
"""
        led_menu_aware.text = led_menu_aware_code
        led_menu_aware.nodeX = led_go_out.nodeX + 200
        led_menu_aware.nodeY = led_go_out.nodeY
        print(f"  ✓ Created led_menu_aware Script CHOP")

    print("\n  MANUAL INTEGRATION REQUIRED:")
    print("  1. In your led_const CHOP, find or create channel 'btn_21'")
    print("  2. Set its expression to:")
    print(f"     op('{VPLAYER_PATH}/led_menu_aware')[0] if op('{VPLAYER_PATH}/led_menu_aware').numChans > 0 else 0")
    print("  3. Or use a Math/Logic CHOP to merge vplayer LED with Eos LED")
    print("  4. Priority: Menu 5 active → vplayer LED, else → Eos LED")

# ==============================================================================
# STEP 4: Test LED Output
# ==============================================================================

print("\n[4/4] Testing LED output...")

if vplayer:
    print("\n  Quick LED Tests (run manually):")
    print("  # Test RECORD mode (should blink):")
    print(f"  op('{VPLAYER_PATH}/state')['mode'] = 1")
    print()
    print("  # Test FOLLOW Idle (should be dark green):")
    print(f"  op('{VPLAYER_PATH}/state')['mode'] = 0")
    print(f"  op('{VPLAYER_PATH}/eos_state')['progress'] = 0")
    print()
    print("  # Test FOLLOW Fahrt (should be bright green):")
    print(f"  op('{VPLAYER_PATH}/state')['mode'] = 0")
    print(f"  op('{VPLAYER_PATH}/eos_state')['progress'] = 0.5")
    print()
    print("  # Read current LED value:")
    print(f"  print(op('{VPLAYER_PATH}/led_go_out')['btn_21'].eval())")

# ==============================================================================
# COMPLETION
# ==============================================================================

print("\n" + "=" * 80)
print("LED INTEGRATION SETUP COMPLETE!")
print("=" * 80)
print("\nComponents:")
print(f"  VPlayer LED Out: {VPLAYER_PATH}/led_go_out")
print(f"  Menu-Aware Switch: {VPLAYER_PATH}/led_menu_aware")
print(f"  LED Constant: {LED_CONST_PATH if led_const else 'NOT FOUND'}")
print(f"  Driver LED: {DRIVER_LED_PATH if driver_led else 'NOT FOUND'}")
print("\nLED States:")
print("  FOLLOW Idle (progress <0.01 or >0.99): Dark green (value ~20)")
print("  FOLLOW Fahrt (0.01 < progress < 0.99): Bright green (value ~100)")
print("  RECORD: Blinking green (100 ↔ 0 at 2Hz)")
print("\nManual Integration Steps:")
print("  See instructions above for connecting to led_const")
print("\nFor detailed guide, see: LED_FEEDBACK_GUIDE.md")
print("=" * 80)
