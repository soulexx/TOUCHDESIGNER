"""
MASTER VPLAYER SETUP SCRIPT
Runs all setup scripts in sequence to build complete vplayer system

Usage in TouchDesigner:
1. Open MIDICRAFT_to_EOS_1.1.toe
2. Open Textport (Alt+T)
3. Run: exec(open('c:\\_DEV\\TOUCHDESIGNER\\SETUP_VPLAYER.py').read())
4. Wait for completion (1-2 minutes)
5. Follow post-setup instructions

Author: Claude Code Agent
Version: 1.0
"""

import os
import time

print()
print("╔" + "=" * 78 + "╗")
print("║" + " " * 20 + "VPLAYER AUTOMATIC SETUP" + " " * 35 + "║")
print("║" + " " * 15 + "Complete TouchDesigner Video Player Build" + " " * 22 + "║")
print("╚" + "=" * 78 + "╝")
print()

# ==============================================================================
# Configuration
# ==============================================================================

SCRIPTS_DIR = 'c:\\_DEV\\TOUCHDESIGNER'
SETUP_SCRIPTS = [
    ('build_vplayer.py', 'Building VPlayer Component'),
    ('setup_osc_in.py', 'Configuring OSC Input'),
    ('setup_led_integration.py', 'Integrating LED Feedback'),
]

VALIDATION_SCRIPT = 'validate_vplayer.py'

# ==============================================================================
# Pre-flight Checks
# ==============================================================================

print("Pre-flight Checks:")
print("-" * 80)

# Check TouchDesigner is running
try:
    project = op('/project1')
    if project:
        print("  ✓ TouchDesigner project loaded")
    else:
        print("  ✗ ERROR: Cannot access /project1")
        print("    Make sure you're running this inside TouchDesigner!")
        raise Exception("Not running in TouchDesigner")
except:
    print("  ✗ ERROR: Not running inside TouchDesigner")
    print("    This script must be run from TouchDesigner Textport!")
    raise

# Check scripts exist
all_scripts_exist = True
for script_file, desc in SETUP_SCRIPTS + [(VALIDATION_SCRIPT, 'Validation')]:
    script_path = os.path.join(SCRIPTS_DIR, script_file)
    if os.path.exists(script_path):
        print(f"  ✓ Found {script_file}")
    else:
        print(f"  ✗ Missing {script_file}")
        all_scripts_exist = False

if not all_scripts_exist:
    print("\n  ERROR: Some setup scripts are missing!")
    print(f"  Check directory: {SCRIPTS_DIR}")
    raise Exception("Missing setup scripts")

# Check vplayer_scripts directory
vplayer_scripts_dir = os.path.join(SCRIPTS_DIR, 'vplayer_scripts')
if os.path.exists(vplayer_scripts_dir):
    script_files = ['osc_event_handler.py', 'marker_write.py', 'marker_delete.py', 'marker_lookup.py']
    missing_scripts = []
    for script in script_files:
        if not os.path.exists(os.path.join(vplayer_scripts_dir, script)):
            missing_scripts.append(script)

    if missing_scripts:
        print(f"  ⚠ Warning: Missing vplayer_scripts: {', '.join(missing_scripts)}")
    else:
        print(f"  ✓ All vplayer_scripts found")
else:
    print(f"  ⚠ Warning: vplayer_scripts directory not found")

print()

# ==============================================================================
# User Confirmation
# ==============================================================================

print("This script will:")
print("  1. Create /project1/media/vplayer component")
print("  2. Configure OSC In for Eos feedback")
print("  3. Integrate LED feedback system")
print("  4. Run validation tests")
print()
print("WARNING: This will DELETE any existing /project1/media/vplayer component!")
print()

# Note: TouchDesigner Python doesn't support input(), so we proceed automatically
print("Proceeding with automatic setup in 3 seconds...")
print("(Press Ctrl+C in Textport to cancel)")
time.sleep(3)

# ==============================================================================
# Run Setup Scripts
# ==============================================================================

print("\n" + "=" * 80)
print("RUNNING SETUP SCRIPTS")
print("=" * 80)

errors = []

for i, (script_file, description) in enumerate(SETUP_SCRIPTS, 1):
    print(f"\n[{i}/{len(SETUP_SCRIPTS)}] {description}")
    print("-" * 80)

    script_path = os.path.join(SCRIPTS_DIR, script_file)

    try:
        # Execute script
        with open(script_path, 'r', encoding='utf-8') as f:
            script_code = f.read()

        exec(script_code, globals())

        print(f"\n✓ {description} completed successfully")

    except Exception as e:
        error_msg = f"Error in {script_file}: {str(e)}"
        print(f"\n✗ {error_msg}")
        errors.append(error_msg)

        # Ask if should continue
        print("\nContinuing with next script...")
        time.sleep(2)

# ==============================================================================
# Run Validation
# ==============================================================================

print("\n" + "=" * 80)
print("RUNNING VALIDATION")
print("=" * 80)

validation_path = os.path.join(SCRIPTS_DIR, VALIDATION_SCRIPT)

try:
    with open(validation_path, 'r', encoding='utf-8') as f:
        validation_code = f.read()

    exec(validation_code, globals())

except Exception as e:
    print(f"\n✗ Validation error: {e}")
    errors.append(f"Validation failed: {e}")

# ==============================================================================
# Final Summary
# ==============================================================================

print("\n" + "╔" + "=" * 78 + "╗")
print("║" + " " * 30 + "SETUP COMPLETE!" + " " * 33 + "║")
print("╚" + "=" * 78 + "╝")

if errors:
    print("\n⚠ SETUP COMPLETED WITH ERRORS:")
    for error in errors:
        print(f"  - {error}")
    print("\nPlease review errors above and run individual scripts if needed.")
else:
    print("\n✓ ALL SETUP STEPS COMPLETED SUCCESSFULLY!")

print("\n" + "=" * 80)
print("POST-SETUP CHECKLIST")
print("=" * 80)

print("""
1. Load Video File
   - Navigate to /project1/media/vplayer/moviefilein1
   - Set 'File' parameter to your video file path
   - Verify video loads (check thumbnail)

2. Configure Eos OSC Output
   - On Eos console: Setup → System → Show Control → OSC
   - OSC TX IP: [Your TouchDesigner Computer IP]
   - OSC TX Port: 7001
   - Enable "Send Feedback"
   - Test: Press GO on Eos, check Textport for [eos_event] messages

3. Test MIDI Faders (Menu 5)
   - Switch to Menu 5 on MIDICRAFT ENC
   - Fader 1: Scrub video position
   - Fader 2: Change playback speed
   - Fader 3: Adjust volume
   - All faders should respond immediately

4. Test Mode Toggle
   - Long press GO button (~0.7s)
   - LED should start blinking (RECORD mode)
   - Long press GO again
   - LED should stop blinking (FOLLOW mode)

5. Record Markers (RECORD Mode)
   - Enter RECORD mode (GO long press)
   - Play video to desired position
   - Press GO short → Marker created for pending cue
   - Verify marker appears in /project1/media/vplayer/markers table

6. Test Video Jump (FOLLOW Mode)
   - Enter FOLLOW mode (GO long press)
   - Press GO on Eos console
   - Video should jump to marker (if exists)
   - Check Textport for "[eos_event] JUMP" message

7. Verify LED States
   - FOLLOW Idle: Dark green LED
   - FOLLOW Fahrt: Bright green LED (during fade)
   - RECORD: Blinking green LED
""")

print("=" * 80)
print("QUICK REFERENCE")
print("=" * 80)

print("""
Component Location: /project1/media/vplayer

Key Components:
  - state           : Player state (mode, speed, volume, loop)
  - eos_state       : Eos feedback (active/pending cue, progress)
  - markers         : Marker table (key, pos_s, label)
  - moviefilein1    : Video player TOP
  - audiodeviceout1 : Audio output CHOP
  - led_go_out      : LED feedback for GO button

Manual Tests:
  # Test RECORD blink
  op('/project1/media/vplayer/state')['mode'] = 1

  # Test FOLLOW Fahrt
  op('/project1/media/vplayer/state')['mode'] = 0
  op('/project1/media/vplayer/eos_state')['progress'] = 0.5

Documentation:
  - VPLAYER_README.md         : Overview & quick start
  - VPLAYER_BUILD_GUIDE.md    : Detailed build guide
  - OSC_IN_GUIDE.md           : OSC configuration
  - LED_FEEDBACK_GUIDE.md     : LED integration
""")

print("=" * 80)
print("TROUBLESHOOTING")
print("=" * 80)

print("""
If something doesn't work:

1. Run validation again:
   exec(open('c:\\_DEV\\TOUCHDESIGNER\\validate_vplayer.py').read())

2. Check Textport for error messages

3. Verify network connectivity (for OSC):
   ping [Eos Console IP]

4. Re-run specific setup script:
   exec(open('c:\\_DEV\\TOUCHDESIGNER\\build_vplayer.py').read())

5. Check individual guides in documentation folder

6. Verify Menu 5 is active:
   op('/project1').fetch('ACTIVE_MENU')
   # Should return 5
""")

print("\n" + "=" * 80)
print("Setup complete! Check components at: /project1/media/vplayer")
print("=" * 80)
print()
