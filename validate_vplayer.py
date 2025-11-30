"""
VPlayer Validation Script
Comprehensive check of all vplayer components and connections

Usage:
1. Open your TouchDesigner project
2. After running all setup scripts
3. Run: exec(open('c:\\_DEV\\TOUCHDESIGNER\\validate_vplayer.py').read())

Author: Claude Code Agent
Version: 1.0
"""

print("=" * 80)
print("VPLAYER VALIDATION")
print("=" * 80)

# ==============================================================================
# Configuration
# ==============================================================================

VPLAYER_PATH = '/project1/media/vplayer'

# Test results
tests_passed = 0
tests_failed = 0
warnings = 0

def test(name, condition, error_msg="", warning=False):
    """Run a test and track results"""
    global tests_passed, tests_failed, warnings

    if condition:
        print(f"  ✓ {name}")
        tests_passed += 1
        return True
    else:
        if warning:
            print(f"  ⚠ {name}: {error_msg}")
            warnings += 1
        else:
            print(f"  ✗ {name}: {error_msg}")
            tests_failed += 1
        return False

# ==============================================================================
# Section 1: Base Component
# ==============================================================================

print("\n[1/8] Base Component")

vplayer = op(VPLAYER_PATH)
test("VPlayer component exists", vplayer is not None, f"Not found at {VPLAYER_PATH}")

if vplayer:
    test("VPlayer is Base COMP", vplayer.type == baseCOMP, f"Wrong type: {vplayer.type}")

# ==============================================================================
# Section 2: State CHOPs
# ==============================================================================

print("\n[2/8] State CHOPs")

if vplayer:
    state = vplayer.op('state')
    test("state CHOP exists", state is not None, "Missing state CHOP")

    if state:
        test("state has 5 channels", state.numChans >= 5, f"Has {state.numChans} channels")
        test("state has 'mode' channel", 'mode' in [state.chan(i).name for i in range(state.numChans)])
        test("state has 'speed' channel", 'speed' in [state.chan(i).name for i in range(state.numChans)])
        test("state has 'volume' channel", 'volume' in [state.chan(i).name for i in range(state.numChans)])

    eos_state = vplayer.op('eos_state')
    test("eos_state CHOP exists", eos_state is not None, "Missing eos_state CHOP")

    if eos_state:
        test("eos_state has 5 channels", eos_state.numChans >= 5, f"Has {eos_state.numChans} channels")
        test("eos_state has 'active_cue' channel", 'active_cue' in [eos_state.chan(i).name for i in range(eos_state.numChans)])
        test("eos_state has 'pending_cue' channel", 'pending_cue' in [eos_state.chan(i).name for i in range(eos_state.numChans)])
        test("eos_state has 'progress' channel", 'progress' in [eos_state.chan(i).name for i in range(eos_state.numChans)])

# ==============================================================================
# Section 3: Markers Table
# ==============================================================================

print("\n[3/8] Markers Table")

if vplayer:
    markers = vplayer.op('markers')
    test("markers DAT exists", markers is not None, "Missing markers DAT")

    if markers:
        test("markers has 3 columns", markers.numCols == 3, f"Has {markers.numCols} columns")
        test("markers has header row", markers.numRows >= 1, "No header row")

        if markers.numCols >= 3 and markers.numRows >= 1:
            header = [markers[0, i].val for i in range(3)]
            test("markers has 'key' column", 'key' in header)
            test("markers has 'pos_s' column", 'pos_s' in header)
            test("markers has 'label' column", 'label' in header)

# ==============================================================================
# Section 4: Video & Audio Chain
# ==============================================================================

print("\n[4/8] Video & Audio Chain")

if vplayer:
    moviefilein1 = vplayer.op('moviefilein1')
    test("moviefilein1 TOP exists", moviefilein1 is not None, "Missing moviefilein1 TOP")

    if moviefilein1:
        test("moviefilein1 is Movie File In TOP", moviefilein1.type == moviefileinTOP)
        test("moviefilein1 play is ON", moviefilein1.par.play.eval(), "Play is OFF", warning=True)
        test("moviefilein1 speed has expression", len(moviefilein1.par.speed.expr) > 0, "Speed not bound to state", warning=True)

    null_vid1 = vplayer.op('null_vid1')
    test("null_vid1 TOP exists", null_vid1 is not None, "Missing null_vid1 TOP")

    if null_vid1 and moviefilein1:
        test("null_vid1 connected to moviefilein1", null_vid1.inputs[0] == moviefilein1, "Not connected")

    out1 = vplayer.op('out1')
    test("out1 TOP exists", out1 is not None, "Missing out1 TOP")

    if out1 and null_vid1:
        test("out1 connected to null_vid1", out1.inputs[0] == null_vid1, "Not connected")

    audiomovie1 = vplayer.op('audiomovie1')
    test("audiomovie1 CHOP exists", audiomovie1 is not None, "Missing audiomovie1 CHOP")

    if audiomovie1 and moviefilein1:
        test("audiomovie1 references moviefilein1", audiomovie1.par.top.eval() == moviefilein1, "Wrong TOP reference")

    audiodeviceout1 = vplayer.op('audiodeviceout1')
    test("audiodeviceout1 CHOP exists", audiodeviceout1 is not None, "Missing audiodeviceout1 CHOP")

    if audiodeviceout1:
        test("audiodeviceout1 volume has expression", len(audiodeviceout1.par.volume.expr) > 0, "Volume not bound", warning=True)

    info_video = vplayer.op('info_video')
    test("info_video CHOP exists", info_video is not None, "Missing info_video CHOP")

# ==============================================================================
# Section 5: Fader Inputs
# ==============================================================================

print("\n[5/8] Fader Input CHOPs")

if vplayer:
    scrub_input = vplayer.op('scrub_input')
    test("scrub_input CHOP exists", scrub_input is not None, "Missing scrub_input CHOP")

    scrub_to_seconds = vplayer.op('scrub_to_seconds')
    test("scrub_to_seconds CHOP exists", scrub_to_seconds is not None, "Missing scrub_to_seconds CHOP")

    if scrub_to_seconds and scrub_input:
        test("scrub_to_seconds connected to scrub_input", scrub_to_seconds.inputs[0] == scrub_input, "Not connected")

    scrub_execute = vplayer.op('scrub_execute')
    test("scrub_execute DAT exists", scrub_execute is not None, "Missing scrub_execute DAT")

    if scrub_execute:
        test("scrub_execute has code", len(scrub_execute.text) > 100, "Empty or minimal code")
        test("scrub_execute has onValueChange", 'onValueChange' in scrub_execute.text)

    speed_input = vplayer.op('speed_input')
    test("speed_input CHOP exists", speed_input is not None, "Missing speed_input CHOP")

    volume_input = vplayer.op('volume_input')
    test("volume_input CHOP exists", volume_input is not None, "Missing volume_input CHOP")

# ==============================================================================
# Section 6: Scripts
# ==============================================================================

print("\n[6/8] Script DATs")

if vplayer:
    osc_event_handler = vplayer.op('osc_event_handler')
    test("osc_event_handler DAT exists", osc_event_handler is not None, "Missing osc_event_handler DAT")

    if osc_event_handler:
        test("osc_event_handler has code", len(osc_event_handler.text) > 500, "Empty or minimal code")
        test("osc_event_handler has on_active_cue_change", 'on_active_cue_change' in osc_event_handler.text)
        test("osc_event_handler has on_pending_cue_change", 'on_pending_cue_change' in osc_event_handler.text)
        test("osc_event_handler has on_osc_message", 'on_osc_message' in osc_event_handler.text)

    marker_write = vplayer.op('marker_write')
    test("marker_write DAT exists", marker_write is not None, "Missing marker_write DAT")

    if marker_write:
        test("marker_write has code", len(marker_write.text) > 500, "Empty or minimal code")
        test("marker_write has write_marker function", 'write_marker' in marker_write.text)

    marker_delete = vplayer.op('marker_delete')
    test("marker_delete DAT exists", marker_delete is not None, "Missing marker_delete DAT")

    if marker_delete:
        test("marker_delete has delete_marker function", 'delete_marker' in marker_delete.text)

    marker_lookup = vplayer.op('marker_lookup')
    test("marker_lookup DAT exists", marker_lookup is not None, "Missing marker_lookup DAT")

    if marker_lookup:
        test("marker_lookup has jump functions", 'jump_to_marker' in marker_lookup.text)

# ==============================================================================
# Section 7: LED Feedback
# ==============================================================================

print("\n[7/8] LED Feedback CHOPs")

if vplayer:
    led_blink_lfo = vplayer.op('led_blink_lfo')
    test("led_blink_lfo CHOP exists", led_blink_lfo is not None, "Missing led_blink_lfo CHOP")

    if led_blink_lfo:
        test("led_blink_lfo frequency is 2Hz", abs(led_blink_lfo.par.freq.eval() - 2.0) < 0.1, f"Freq: {led_blink_lfo.par.freq.eval()}", warning=True)

    led_values = vplayer.op('led_values')
    test("led_values CHOP exists", led_values is not None, "Missing led_values CHOP")

    led_state_select = vplayer.op('led_state_select')
    test("led_state_select CHOP exists", led_state_select is not None, "Missing led_state_select CHOP")

    if led_state_select:
        test("led_state_select has script", len(led_state_select.text) > 200 if hasattr(led_state_select, 'text') else False, "Empty script", warning=True)

    led_go_out = vplayer.op('led_go_out')
    test("led_go_out CHOP exists", led_go_out is not None, "Missing led_go_out CHOP")

    if led_go_out:
        test("led_go_out has btn_21 channel", 'btn_21' in [led_go_out.chan(i).name for i in range(led_go_out.numChans)] if led_go_out.numChans > 0 else False)
        test("led_go_out has expression", len(led_go_out.par.value0.expr) > 0, "No expression binding", warning=True)

    led_flash_timer = vplayer.op('led_flash_timer')
    test("led_flash_timer CHOP exists", led_flash_timer is not None, "Missing led_flash_timer CHOP", warning=True)

# ==============================================================================
# Section 8: External Integration
# ==============================================================================

print("\n[8/8] External Integration")

# Check menu_engine.py
menu_engine = op('/project1/layers/menus/menu_engine')
if not menu_engine:
    menu_engine = op('/project1/menus/menu_engine')

test("menu_engine exists", menu_engine is not None, "Cannot find menu_engine", warning=True)

if menu_engine and hasattr(menu_engine, 'module'):
    test("menu_engine has _handle_vplayer_command", hasattr(menu_engine.module, '_handle_vplayer_command'), "Function not found", warning=True)

# Check OSC In
osc_in = op('/project1/io/oscin_eos')
test("OSC In DAT exists", osc_in is not None, "Not configured yet", warning=True)

if osc_in:
    test("OSC In is active", osc_in.par.active.eval(), "OSC In not active", warning=True)
    test("OSC In has callback", 'onReceiveOSC' in osc_in.text if hasattr(osc_in, 'text') else False, "No callback installed", warning=True)

# Check LED integration
led_const = op('/project1/io/led_const')
test("LED Constant exists", led_const is not None, "Not configured yet", warning=True)

# ==============================================================================
# RESULTS SUMMARY
# ==============================================================================

print("\n" + "=" * 80)
print("VALIDATION RESULTS")
print("=" * 80)

total_tests = tests_passed + tests_failed
pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"\nTests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Warnings: {warnings}")
print(f"Pass Rate: {pass_rate:.1f}%")

if tests_failed == 0 and warnings == 0:
    print("\n✓ ALL TESTS PASSED!")
    print("VPlayer is fully configured and ready to use.")
elif tests_failed == 0:
    print("\n✓ CORE TESTS PASSED")
    print("VPlayer is functional but has some optional components missing.")
    print("Review warnings above for optimization.")
else:
    print("\n✗ SOME TESTS FAILED")
    print("VPlayer has missing or misconfigured components.")
    print("Review failed tests above and run setup scripts again.")

print("\nNext Steps:")
if tests_failed > 0:
    print("  1. Run build_vplayer.py to create missing components")
    print("  2. Run setup_osc_in.py to configure OSC input")
    print("  3. Run setup_led_integration.py for LED feedback")
    print("  4. Run this validation again")
else:
    print("  1. Load a video file in moviefilein1 parameter")
    print("  2. Configure Eos OSC TX (IP, Port 7001)")
    print("  3. Test with MIDI faders in Menu 5")
    print("  4. Create markers in RECORD mode")
    print("  5. Test video jumping in FOLLOW mode")

print("\nManual Tests:")
print("  # Test RECORD mode blink:")
print(f"  op('{VPLAYER_PATH}/state')['mode'] = 1")
print(f"  # LED should blink (check led_go_out value)")
print()
print("  # Test FOLLOW Fahrt:")
print(f"  op('{VPLAYER_PATH}/state')['mode'] = 0")
print(f"  op('{VPLAYER_PATH}/eos_state')['progress'] = 0.5")
print(f"  # LED should be bright green (~100)")

print("\n" + "=" * 80)
