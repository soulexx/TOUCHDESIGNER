"""
Automatic OSC In Setup for VPlayer
Configures OSC In DAT to receive Eos feedback and route to vplayer

Usage:
1. Open your TouchDesigner project
2. Make sure vplayer component exists at /project1/media/vplayer
3. Run: exec(open('c:\\_DEV\\TOUCHDESIGNER\\setup_osc_in.py').read())

Author: Claude Code Agent
Version: 1.0
"""

print("=" * 80)
print("OSC IN AUTOMATIC SETUP")
print("=" * 80)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

OSC_IN_PATH = '/project1/io/oscin_eos'  # Adjust if your OSC In is elsewhere
VPLAYER_PATH = '/project1/media/vplayer'
OSC_PORT = 7001  # Default Eos OSC TX port

# ==============================================================================
# STEP 1: Find or Create OSC In DAT
# ==============================================================================

print("\n[1/3] Finding/Creating OSC In DAT...")

# Try to find existing OSC In
oscin = op(OSC_IN_PATH)

if not oscin:
    # Create new one
    print(f"  - OSC In not found at {OSC_IN_PATH}")
    parent_path = '/project1/io'
    parent = op(parent_path)

    if not parent:
        print(f"  ERROR: Parent {parent_path} not found!")
        print("  Please adjust OSC_IN_PATH in script or create /project1/io")
    else:
        oscin = parent.create(oscinDAT, 'oscin_eos')
        oscin.par.protocol = 'UDP'
        oscin.par.port = OSC_PORT
        oscin.par.active = True
        print(f"  ✓ Created OSC In DAT at {oscin.path}")
else:
    print(f"  ✓ Found existing OSC In at {oscin.path}")

# Configure OSC In parameters
if oscin:
    oscin.par.protocol = 'UDP'
    oscin.par.port = OSC_PORT
    oscin.par.active = True
    print(f"  ✓ Configured: Port {OSC_PORT}, Protocol UDP, Active ON")

# ==============================================================================
# STEP 2: Add Callback Script
# ==============================================================================

print("\n[2/3] Adding OSC callback script...")

if oscin:
    # Check if vplayer exists
    vplayer = op(VPLAYER_PATH)
    if not vplayer:
        print(f"  ERROR: vplayer not found at {VPLAYER_PATH}")
        print("  Please run build_vplayer.py first!")
    else:
        # Add onReceiveOSC callback
        callback_code = """# OSC In Callback - Routes messages to vplayer
def onReceiveOSC(dat, rowIndex, message, bytes):
    '''
    Called when OSC message received
    message[0] = address (string)
    message[1:] = arguments (list)
    '''
    try:
        address = message[0] if len(message) > 0 else ''
        args = message[1:] if len(message) > 1 else []

        # Route to vplayer OSC event handler
        handler = op('/project1/media/vplayer/osc_event_handler')
        if handler and hasattr(handler, 'module') and handler.module:
            handler.module.on_osc_message(address, *args)

    except Exception as exc:
        print(f"[OSC In] Error processing message: {exc}")
        import traceback
        traceback.print_exc()

def onReceiveCHOP(dat, rowIndex, message, bytes):
    return

def onReceiveCHOPString(dat, rowIndex, message, bytes):
    return

def onSendOSC(dat, rowIndex, message, bytes):
    return
"""

        oscin.text = callback_code
        print(f"  ✓ Added onReceiveOSC callback to {oscin.path}")
        print(f"  ✓ Callback routes to: {VPLAYER_PATH}/osc_event_handler")

# ==============================================================================
# STEP 3: Test Configuration
# ==============================================================================

print("\n[3/3] Testing configuration...")

if oscin:
    # Check if port is listening
    if oscin.par.active.eval():
        print(f"  ✓ OSC In is ACTIVE on port {oscin.par.port.eval()}")
    else:
        print(f"  ⚠ OSC In is INACTIVE - enable 'Active' parameter")

    # Check callback exists
    if oscin.text and 'onReceiveOSC' in oscin.text:
        print(f"  ✓ Callback function installed")
    else:
        print(f"  ⚠ Callback function missing!")

    # Check vplayer handler exists
    handler = op(f"{VPLAYER_PATH}/osc_event_handler")
    if handler:
        print(f"  ✓ VPlayer OSC handler found")
    else:
        print(f"  ⚠ VPlayer OSC handler missing!")

# ==============================================================================
# COMPLETION
# ==============================================================================

print("\n" + "=" * 80)
print("OSC IN SETUP COMPLETE!")
print("=" * 80)
print("\nConfiguration:")
print(f"  OSC In DAT: {OSC_IN_PATH if oscin else 'NOT CREATED'}")
print(f"  Port: {OSC_PORT}")
print(f"  Protocol: UDP")
print(f"  Routes to: {VPLAYER_PATH}/osc_event_handler")
print("\nNext steps:")
print("1. Configure Eos OSC TX:")
print("   - IP: Your TouchDesigner computer IP")
print("   - Port: 7001")
print("   - Enable OSC Feedback")
print("2. Test by pressing GO on Eos")
print("3. Check textport for '[eos_event]' messages")
print("\nManual test:")
print("  # Send test OSC message from Eos or another source")
print("  # You should see messages in textport when received")
print("\nFor detailed guide, see: OSC_IN_GUIDE.md")
print("=" * 80)
